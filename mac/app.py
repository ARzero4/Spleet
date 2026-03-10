"""Spleet entry point for macOS builds and local runs."""
import logging
import multiprocessing
import os
import sys
import os
from pathlib import Path

# Ensure 'shared' is importable in both dev and frozen (PyInstaller) modes
if getattr(sys, 'frozen', False):
    _meipass_shared = os.path.join(getattr(sys, '_MEIPASS', ''), 'shared')
    if os.path.isdir(_meipass_shared) and _meipass_shared not in sys.path:
        sys.path.insert(0, _meipass_shared)
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
from pathlib import Path


def _resolve_base_path() -> str:
    """Return resource root for development and PyInstaller runtime."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.abspath("."))
    return str(Path(__file__).resolve().parents[1] / "shared")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHARED_PATH = PROJECT_ROOT / "shared"
if str(SHARED_PATH) not in sys.path:
    # Ensure top-level imports like "from ui..." resolve from shared/
    sys.path.insert(0, str(SHARED_PATH))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-18s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger("spleet")

# Required for PyInstaller + multiprocessing (PyTorch/Demucs)
multiprocessing.freeze_support()

# Demucs subprocess mode
if "--run-demucs" in sys.argv:
    logger.info("Entering Demucs subprocess mode")
    try:
        from demucs.separate import main as demucs_main

        idx = sys.argv.index("--run-demucs")
        demucs_args = sys.argv[idx + 1 :]
        logger.info("Demucs args: %s", demucs_args)
        result = demucs_main(demucs_args)
        sys.exit(result if isinstance(result, int) else 0)
    except SystemExit as exc:
        sys.exit(exc.code)
    except Exception as exc:
        logger.exception("Demucs subprocess error: %s", exc)
        sys.exit(1)

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from shared.ui.main_window import MainWindow

if __name__ == "__main__":
    logger.info("Starting Spleet application")
    app = QApplication(sys.argv)

    base_path = _resolve_base_path()
    icns_path = os.path.join(base_path, "assets", "logo.icns")
    png_path = os.path.join(base_path, "assets", "logo.png")
    ico_path = os.path.join(base_path, "assets", "logo.ico")
    if os.path.exists(icns_path):
        app.setWindowIcon(QIcon(icns_path))
    elif os.path.exists(png_path):
        app.setWindowIcon(QIcon(png_path))
    elif os.path.exists(ico_path):
        app.setWindowIcon(QIcon(ico_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
