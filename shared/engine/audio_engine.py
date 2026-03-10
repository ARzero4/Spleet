"""AudioEngine — builds the Demucs subprocess command."""
import os
import sys
import logging
from pathlib import Path

# ── Encoding / backend env vars (set early, before any torch import) ──
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["TORCHAUDIO_USE_SOUNDFILE"] = "1"

# ── Model cache paths ────────────────────────────────────────────
if getattr(sys, "frozen", False):
    BASE_PATH = getattr(sys, "_MEIPASS", os.path.abspath("."))
else:
    # shared/engine/audio_engine.py -> shared/
    BASE_PATH = str(Path(__file__).resolve().parents[1])
MODELS_BASE = os.path.join(BASE_PATH, "models")

os.environ["TORCH_HOME"] = MODELS_BASE
os.environ["DEMUCS_CACHE"] = os.path.join(MODELS_BASE, "hub")
os.environ["XDG_CACHE_HOME"] = os.path.join(MODELS_BASE, ".cache")

logger = logging.getLogger(__name__)
logger.info("Model cache: %s", MODELS_BASE)


class AudioEngine:
    """Builds the command list used to invoke Demucs as a subprocess."""

    VALID_MODES = ("vocals", "full")
    VALID_QUALITY = ("quick", "quality")

    # ── Validation ────────────────────────────────────────────────
    @staticmethod
    def validate_inputs(input_file: str, output_dir: str, mode: str, quality: str):
        """Raise on any invalid / inaccessible path or bad parameter."""
        if not input_file:
            raise ValueError("Input file path is required")
        if not os.path.isfile(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        if not os.access(input_file, os.R_OK):
            raise PermissionError(f"Cannot read input file: {input_file}")

        if not output_dir:
            raise ValueError("Output directory is required")
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as exc:
            raise PermissionError(f"Cannot create output directory: {exc}") from exc
        if not os.access(output_dir, os.W_OK):
            raise PermissionError(f"Cannot write to output directory: {output_dir}")

        if mode not in AudioEngine.VALID_MODES:
            raise ValueError(f"Invalid mode '{mode}'. Must be one of: {AudioEngine.VALID_MODES}")
        if quality not in AudioEngine.VALID_QUALITY:
            raise ValueError(f"Invalid quality '{quality}'. Must be one of: {AudioEngine.VALID_QUALITY}")

    # ── Command builder ───────────────────────────────────────────
    def run_demucs(self, input_file: str, output_dir: str, mode: str, quality: str) -> list[str]:
        """Return the command list for ``subprocess.Popen``."""
        self.validate_inputs(input_file, output_dir, mode, quality)
        logger.info("Building Demucs cmd: file=%s mode=%s quality=%s", input_file, mode, quality)

        # Frozen (PyInstaller) vs. development
        if getattr(sys, "frozen", False):
            cmd = [os.path.abspath(sys.argv[0]), "--run-demucs"]
        else:
            cmd = [sys.executable, sys.argv[0], "--run-demucs"]

        # Model selection
        cmd += ["-n", "htdemucs_ft" if quality == "quality" else "htdemucs"]

        # Stem mode
        if mode == "vocals":
            cmd += ["--two-stems", "vocals"]

        cmd += ["-d", "cpu", "-o", output_dir, input_file]
        logger.info("Command: %s", " ".join(cmd))
        return cmd
