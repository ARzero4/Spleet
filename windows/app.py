"""Spleet — Offline Stem Splitter
Entry point that also serves as the Demucs subprocess target.
"""
import sys
import os
from pathlib import Path

# Ensure project root is in sys.path so 'shared' is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import os
import multiprocessing
import logging
from pathlib import Path


def _resolve_base_path() -> str:
    """Return resource root for development and PyInstaller runtime."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.abspath("."))
    # windows/app.py -> project_root/shared
    return str(Path(__file__).resolve().parents[1] / "shared")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHARED_PATH = PROJECT_ROOT / "shared"
if str(SHARED_PATH) not in sys.path:
    # Ensure top-level imports like "from ui..." resolve from shared/
    sys.path.insert(0, str(SHARED_PATH))

# ── Logging (once, at the top) ────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-18s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger("spleet")

# Required for PyInstaller + multiprocessing (PyTorch/Demucs)
multiprocessing.freeze_support()

# ── Demucs subprocess mode ────────────────────────────────────────
if "--run-demucs" in sys.argv:
    logger.info("Entering Demucs subprocess mode")
    try:
        from demucs.separate import main as demucs_main

        idx = sys.argv.index("--run-demucs")
        demucs_args = sys.argv[idx + 1:]
        logger.info("Demucs args: %s", demucs_args)
        result = demucs_main(demucs_args)
        sys.exit(result if isinstance(result, int) else 0)
    except SystemExit as exc:
        sys.exit(exc.code)
    except Exception as exc:
        logger.exception("Demucs subprocess error: %s", exc)
        sys.exit(1)

# ── GUI mode ──────────────────────────────────────────────────────
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from shared.ui.main_window import MainWindow

if __name__ == "__main__":
    logger.info("Starting Spleet application")
    app = QApplication(sys.argv)

    base_path = _resolve_base_path()
    # Prefer .ico for crisp taskbar / title bar icons on Windows
    ico_path = os.path.join(base_path, "assets", "logo.ico")
    png_path = os.path.join(base_path, "assets", "logo.png")
    if os.path.exists(ico_path):
        app.setWindowIcon(QIcon(ico_path))
    elif os.path.exists(png_path):
        app.setWindowIcon(QIcon(png_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
