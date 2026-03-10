"""EngineWorker — runs Demucs in a subprocess, reports accurate progress,
and flattens the output so stems land in one clean folder."""
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from engine.audio_engine import AudioEngine

logger = logging.getLogger(__name__)

# Safety timeout: 60 minutes for very large files
PROCESSING_TIMEOUT = 60 * 60

# htdemucs_ft averages 4 independently-trained "bags" (model variants).
# Each bag processes the full audio and shows its own 0→100 % progress bar,
# so the user would see the bar fill four times.  We track pass resets and
# compute:  overall = (completed_passes × 100 + current %) / total_passes
_PASSES = {"quality": 4, "quick": 1}

# Prevent a console window flash on Windows
_CREATION_FLAGS: int = 0
if sys.platform == "win32":
    _CREATION_FLAGS = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]


class EngineWorker(QObject):
    """Runs Demucs as a child process and emits progress / finished signals."""

    finished = Signal(list, bool, str)   # stems, success, error_message
    progress = Signal(int, str)          # percent (0-100), status text

    def __init__(self, input_file: str, output_dir: str, mode: str, quality: str):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        self.mode = mode
        self.quality = quality
        self.engine = AudioEngine()
        self.process: subprocess.Popen | None = None
        self.should_cancel = False

    # ── Cancellation ──────────────────────────────────────────────
    def cancel(self):
        """Request graceful cancellation; escalate to kill if needed."""
        self.should_cancel = True
        proc = self.process
        if proc is None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
                proc.wait(timeout=2)
            except OSError:
                pass
        except OSError:
            pass

    # ── Main entry (runs on QThread) ──────────────────────────────
    def run(self):  # noqa: C901
        start = time.time()

        # 1. Build command ─────────────────────────────────────────
        try:
            cmd = self.engine.run_demucs(
                self.input_file, self.output_dir, self.mode, self.quality,
            )
        except Exception as exc:
            msg = f"Failed to build command: {exc}"
            logger.error(msg)
            self.progress.emit(0, msg)
            self.finished.emit([], False, msg)
            return

        logger.info("Starting Demucs: %s", " ".join(cmd))

        # 2. Prepare environment ───────────────────────────────────
        env = os.environ.copy()
        if getattr(sys, "frozen", False):
            base = getattr(sys, "_MEIPASS", os.path.abspath("."))
        else:
            # shared/ui/worker.py -> shared/
            base = str(Path(__file__).resolve().parents[1])
        models = os.path.join(base, "models")
        env["TORCH_HOME"] = models
        env["DEMUCS_CACHE"] = os.path.join(models, "hub")
        env["XDG_CACHE_HOME"] = os.path.join(models, ".cache")

        # 3. Launch subprocess ─────────────────────────────────────
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
                creationflags=_CREATION_FLAGS,
            )
        except FileNotFoundError:
            msg = "Demucs executable not found — is Demucs installed?"
            logger.error(msg)
            self.progress.emit(0, msg)
            self.finished.emit([], False, msg)
            return
        except Exception as exc:
            msg = f"Error launching Demucs: {exc}"
            logger.error(msg)
            self.progress.emit(0, msg)
            self.finished.emit([], False, msg)
            return

        if not self.process.stdout:
            self.finished.emit([], False, "Failed to create subprocess output pipe")
            return

        # 4. Stream output & parse progress ────────────────────────
        total_passes = _PASSES.get(self.quality, 1)
        completed_passes = 0
        last_raw = -1
        last_overall = -1
        phase = "Separating audio"

        try:
            for line in self.process.stdout:
                # --- cancellation ---
                if self.should_cancel:
                    logger.info("User cancelled — terminating subprocess")
                    try:
                        self.process.terminate()
                        self.process.wait(timeout=5)
                    except Exception:
                        try:
                            self.process.kill()
                        except OSError:
                            pass
                    self.finished.emit([], False, "Cancelled by user")
                    return

                stripped = line.strip()
                if not stripped:
                    continue
                logger.debug("demucs> %s", stripped)

                # Phase detection
                low = stripped.lower()
                if "saving" in low or "writing" in low:
                    phase = "Saving stems"

                # Percentage parsing
                matches = re.findall(r"(\d+)%", stripped)
                if matches:
                    raw = min(int(matches[-1]), 100)

                    # Detect pass reset: progress drops significantly
                    # (e.g. 95% → 3%) meaning a new bag/pass has started
                    if last_raw >= 80 and raw < 30:
                        completed_passes = min(
                            completed_passes + 1, total_passes - 1,
                        )
                        logger.info(
                            "Pass %d/%d detected", completed_passes + 1, total_passes,
                        )
                    last_raw = raw

                    # Overall progress distributed across all passes
                    overall = min(
                        99, (completed_passes * 100 + raw) // total_passes,
                    )

                    if overall != last_overall:
                        elapsed = time.time() - start
                        if overall > 3:
                            eta = max(0, int((elapsed / overall) * (100 - overall)))
                            status = f"{phase}: {overall}%  —  ~{eta}s left"
                        else:
                            status = f"{phase}…"
                        self.progress.emit(overall, status)
                        last_overall = overall

                # Timeout guard
                if time.time() - start > PROCESSING_TIMEOUT:
                    logger.error("Timeout reached")
                    try:
                        self.process.terminate()
                    except OSError:
                        pass
                    self.finished.emit(
                        [], False,
                        f"Timed out after {PROCESSING_TIMEOUT // 60} min",
                    )
                    return

        except Exception as exc:
            logger.error("Error reading output: %s", exc)
            self.finished.emit([], False, f"Processing error: {exc}")
            return

        # 5. Wait for exit ─────────────────────────────────────────
        try:
            self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            logger.warning("Force-killing after 30 s")
            try:
                self.process.kill()
                self.process.wait(timeout=5)
            except OSError:
                pass
            self.finished.emit([], False, "Process did not exit in time")
            return

        if self.process.returncode != 0 and not self.should_cancel:
            msg = "Separation failed — check that the audio file is valid."
            logger.error("Demucs exited with code %d", self.process.returncode)
            self.progress.emit(0, msg)
            self.finished.emit([], False, msg)
            return

        # 6. Flatten output ────────────────────────────────────────
        # Demucs creates:  output_dir / model_name / song_name / *.wav
        # We want:          output_dir / song_name / *.wav
        stem_files = self._flatten_output()
        logger.info("Done — %d stems", len(stem_files))
        self.finished.emit(stem_files, True, "")

    # ── Helpers ───────────────────────────────────────────────────
    def _flatten_output(self) -> list[str]:
        """Move stems out of the model-name subfolder into one clean folder."""
        song_name = Path(self.input_file).stem
        model = "htdemucs_ft" if self.quality == "quality" else "htdemucs"
        demucs_dir = Path(self.output_dir) / model / song_name
        target_dir = Path(self.output_dir) / song_name

        files: list[str] = []

        if demucs_dir.is_dir() and demucs_dir.resolve() != target_dir.resolve():
            target_dir.mkdir(parents=True, exist_ok=True)
            for f in demucs_dir.iterdir():
                if f.is_file():
                    dest = target_dir / f.name
                    if dest.exists():
                        dest.unlink()
                    shutil.move(str(f), str(dest))
                    files.append(str(dest))
            # Remove the now-empty model-name folder
            model_folder = Path(self.output_dir) / model
            try:
                shutil.rmtree(model_folder)
            except Exception:
                pass
        elif demucs_dir.is_dir():
            # Same path — just collect files in place
            for f in demucs_dir.iterdir():
                if f.is_file():
                    files.append(str(f))
        else:
            # Fallback: walk entire output dir
            for root, _, fnames in os.walk(self.output_dir):
                for fn in fnames:
                    if fn.lower().endswith((".wav", ".mp3", ".flac")):
                        files.append(os.path.join(root, fn))

        return files
