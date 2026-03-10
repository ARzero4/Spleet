"""MainWindow — Spleet v0.2 · dark UI · smooth animations."""
import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QSettings,
    QSize,
    QThread,
    Qt,
    QTimer,
)
from PySide6.QtGui import QFontMetrics, QIcon, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QGraphicsOpacityEffect,
    QGroupBox,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.worker import EngineWorker

logger = logging.getLogger(__name__)

APP_VERSION = "0.2"

# ── Dark palette — neutral grays, no flashy colours ──────────────
_BG       = "#111111"
_SURFACE  = "#1a1a1a"
_RAISED   = "#222222"
_BORDER   = "#2c2c2c"
_TEXT     = "#c8c8c8"
_DIM      = "#606060"
_ACCENT   = "#e07830"   # warm amber
_ACC_HI   = "#f09040"
_GREEN    = "#3a9e6a"
_GREEN_BG = "#162118"
_RED      = "#c94040"
_RED_BG   = "#201414"

# ── Stylesheet ────────────────────────────────────────────────────
_SHEET = f"""
* {{
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}}
QWidget#SpleetMain {{
    background: {_BG};
}}

/* group boxes */
QGroupBox {{
    background: {_SURFACE};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    margin-top: 16px;
    padding: 14px 10px 8px 10px;
    color: {_TEXT};
    font-weight: 600;
    font-size: 12px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {_ACCENT};
    font-size: 10px;
    letter-spacing: 1px;
}}

/* radio buttons */
QRadioButton {{
    color: {_TEXT};
    spacing: 6px;
    padding: 3px 0;
    font-size: 12px;
}}
QRadioButton::indicator {{
    width: 14px; height: 14px;
    border: 2px solid {_DIM};
    border-radius: 9px;
    background: transparent;
}}
QRadioButton::indicator:checked {{
    background: {_ACCENT};
    border-color: {_ACCENT};
}}
QRadioButton::indicator:hover {{ border-color: {_ACC_HI}; }}
QRadioButton:disabled {{ color: {_DIM}; }}

/* buttons */
QPushButton {{
    background: {_RAISED};
    color: {_TEXT};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: 500;
    font-size: 12px;
}}
QPushButton:hover {{
    background: {_BORDER};
    border-color: {_ACCENT};
}}
QPushButton:pressed {{ background: {_ACCENT}; color: #fff; }}
QPushButton:disabled {{
    color: {_DIM}; background: {_BG}; border-color: {_BORDER};
}}

QPushButton#runBtn {{
    background: {_ACCENT};
    color: #fff;
    font-weight: 700;
    font-size: 13px;
    border: none;
    padding: 10px;
    border-radius: 8px;
}}
QPushButton#runBtn:hover    {{ background: {_ACC_HI}; }}
QPushButton#runBtn:disabled {{ background: {_BORDER}; color: {_DIM}; }}

QPushButton#cancelBtn {{
    background: {_RED};
    color: #fff;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 10px;
}}
QPushButton#cancelBtn:hover    {{ background: #d95555; }}
QPushButton#cancelBtn:disabled {{ background: {_BORDER}; color: {_DIM}; }}

/* progress bar */
QProgressBar {{
    border: none;
    border-radius: 5px;
    background: {_RAISED};
    text-align: center;
    color: {_TEXT};
    min-height: 12px;
    max-height: 12px;
    font-size: 9px;
}}
QProgressBar::chunk {{
    border-radius: 5px;
    background: {_ACCENT};
}}

/* labels */
QLabel {{ color: {_TEXT}; }}
QLabel#dimLabel  {{ color: {_DIM}; font-size: 11px; }}
QLabel#statusLabel {{
    color: {_DIM}; font-size: 11px;
    padding: 3px 6px;
    border-radius: 4px;
}}
QLabel#tinyLabel {{ color: {_DIM}; font-size: 9px; }}
"""

# ── Drop-zone styles ─────────────────────────────────────────────
_DROP_EMPTY = f"""QLabel {{
    border: 2px dashed {_DIM};
    border-radius: 10px;
    color: {_DIM};
    font-size: 12px;
    background: {_SURFACE};
    padding: 10px;
}}"""
_DROP_HOVER = f"""QLabel {{
    border: 2px dashed {_ACCENT};
    border-radius: 10px;
    color: {_ACCENT};
    font-size: 12px;
    background: {_RAISED};
    padding: 10px;
}}"""
_DROP_FILLED = f"""QLabel {{
    border: 2px solid {_GREEN};
    border-radius: 10px;
    color: {_GREEN};
    font-size: 12px;
    background: {_GREEN_BG};
    padding: 10px;
}}"""
_DROP_OFF = f"""QLabel {{
    border: 2px dashed {_BORDER};
    border-radius: 10px;
    color: {_BORDER};
    font-size: 12px;
    background: {_BG};
    padding: 10px;
}}"""


# ╭─────────────────────────────────────────────────────────────────╮
# │  DropBox                                                        │
# ╰─────────────────────────────────────────────────────────────────╯
class DropBox(QLabel):
    """Drag-and-drop target for audio / video files."""

    def __init__(self, parent=None, callback=None):
        super().__init__(parent)
        self.callback = callback
        self.file_path: str | None = None
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(70)
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.clear()

    def set_filled(self, file_path: str):
        self.file_path = file_path
        name = os.path.basename(file_path)
        width = max(self.width() - 32, 80)
        elided = QFontMetrics(self.font()).elidedText(name, Qt.ElideMiddle, width)
        self.setText(f"✔  {elided}")
        self.setStyleSheet(_DROP_FILLED)
        self.setToolTip(file_path)

    def clear(self):
        self.file_path = None
        self.setText("Drop audio / video file here")
        self.setStyleSheet(_DROP_EMPTY)
        self.setToolTip("")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(_DROP_HOVER)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._restore()
        event.accept()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path and self.callback:
                self.callback(path)
        else:
            self._restore()

    def mousePressEvent(self, event):
        # Only allow file picker if not processing
        if event.button() == Qt.LeftButton and hasattr(self.parent(), "pick_file"):
            if not getattr(self.parent(), "is_processing", False):
                self.parent().pick_file()
        super().mousePressEvent(event)

    def set_drops_enabled(self, enabled: bool):
        self.setAcceptDrops(enabled)
        if enabled:
            self.setCursor(Qt.PointingHandCursor)
            self._restore()
        else:
            self.setCursor(Qt.ArrowCursor)
            self.setStyleSheet(_DROP_OFF)

    def _restore(self):
        if self.file_path:
            self.set_filled(self.file_path)
        else:
            self.clear()


# ╭─────────────────────────────────────────────────────────────────╮
# │  MainWindow                                                     │
# ╰─────────────────────────────────────────────────────────────────╯
class MainWindow(QWidget):
    ALLOWED_EXT = (
        ".wav", ".mp3", ".flac", ".aac", ".ogg", ".m4a",
        ".mp4", ".mkv", ".mov", ".avi", ".webm",
    )

    def __init__(self):
        super().__init__()
        self.setObjectName("SpleetMain")

        # ── Window icon (use .ico for clear titlebar rendering) ───
        if getattr(sys, "frozen", False):
            base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
        else:
            # shared/ui/main_window.py -> shared/
            base_path = str(Path(__file__).resolve().parents[1])
        ico_path = os.path.join(base_path, "assets", "logo.ico")
        png_path = os.path.join(base_path, "assets", "logo.png")
        icon = QIcon()
        if os.path.exists(ico_path):
            icon.addFile(ico_path, QSize(64, 64))
            icon.addFile(ico_path, QSize(48, 48))
            icon.addFile(ico_path, QSize(32, 32))
            icon.addFile(ico_path, QSize(16, 16))
        elif os.path.exists(png_path):
            icon.addFile(png_path)
        self.setWindowIcon(icon)

        self.setWindowTitle("Spleet")
        self.setAcceptDrops(True)

        # Initial size — allow resizing for animation
        self.setFixedSize(300, 520)  # Start compact

        flags = (
            Qt.Window
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
            | Qt.WindowCloseButtonHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowStaysOnTopHint
        )
        if sys.platform == "win32":
            flags |= Qt.MSWindowsFixedSizeDialogHint
        self.setWindowFlags(flags)
        self.setStyleSheet(_SHEET)

        self.input_file: str | None = None
        self.custom_output: str | None = None
        self.thread: QThread | None = None
        self.worker: EngineWorker | None = None
        self.is_processing = False
        self.model_loaded_once = False
        self.settings = QSettings("Spleet", "Spleet")

        self._prog_anim: QPropertyAnimation | None = None

        self._build_ui()
        self._restore_settings()

    # ── Build UI ──────────────────────────────────────────────────
    def _build_ui(self):
        lay = QVBoxLayout()
        lay.setContentsMargins(14, 12, 14, 10)
        lay.setSpacing(14)  # Increased spacing between all elements

        # Drop zone
        self.drop_box = DropBox(self, callback=self.handle_selected_file)
        lay.addWidget(self.drop_box)

        # File picker
        self.pick_btn = QPushButton("Select Audio / Video File")
        self.pick_btn.clicked.connect(self.pick_file)
        lay.addWidget(self.pick_btn)

        # Separation mode
        grp_mode = QGroupBox("MODE")
        ml = QVBoxLayout()
        ml.setContentsMargins(10, 6, 10, 6)
        ml.setSpacing(2)
        self.rb_vocals = QRadioButton("Vocals + Music")
        self.rb_full   = QRadioButton("Vocals + Drums + Bass + Other")
        self.rb_vocals.setChecked(True)
        ml.addWidget(self.rb_vocals)
        ml.addWidget(self.rb_full)
        grp_mode.setLayout(ml)
        lay.addWidget(grp_mode)

        # Progress area — hidden at startup, only visible during processing
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setVisible(False)
        lay.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(20)
        self.status_label.setVisible(False)
        lay.addWidget(self.status_label)

        # Quality
        grp_q = QGroupBox("QUALITY")
        ql = QVBoxLayout()
        ql.setContentsMargins(10, 6, 10, 6)
        ql.setSpacing(2)
        self.rb_quick   = QRadioButton("Quick — fast, good quality")
        self.rb_quality = QRadioButton("Quality — slow, best vocals")
        self.rb_quick.setChecked(True)
        ql.addWidget(self.rb_quick)
        ql.addWidget(self.rb_quality)
        grp_q.setLayout(ql)
        lay.addWidget(grp_q)

        # Output folder
        self.out_label = QLabel("Output: input file's folder")
        self.out_label.setObjectName("dimLabel")
        self.out_label.setWordWrap(True)
        self.out_btn = QPushButton("Choose Output Folder")
        self.out_btn.clicked.connect(self.pick_output_folder)
        lay.addWidget(self.out_label)
        lay.addWidget(self.out_btn)

        # Action buttons
        self.run_btn = QPushButton("Split Stems")
        self.run_btn.setObjectName("runBtn")
        self.run_btn.setEnabled(False)
        self.run_btn.clicked.connect(self.run_engine)
        lay.addWidget(self.run_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self.cancel_processing)
        lay.addWidget(self.cancel_btn)

        lay.addStretch()

        ver = QLabel(f"v{APP_VERSION}")
        ver.setObjectName("tinyLabel")
        ver.setAlignment(Qt.AlignCenter)
        lay.addWidget(ver)

        self.setLayout(lay)

    # ── Animation helpers ─────────────────────────────────────────
    def _fade_in(self, widget, ms=250):
        """Fade a widget into view."""
        widget.setVisible(True)
        eff = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(eff)
        eff.setOpacity(0.0)
        anim = QPropertyAnimation(eff, b"opacity")
        anim.setDuration(ms)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        anim.start()
        widget.setProperty("_anim", anim)

    def _fade_out(self, widget, ms=250):
        """Fade a widget out then hide it."""
        eff = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(eff)
        eff.setOpacity(1.0)
        anim = QPropertyAnimation(eff, b"opacity")
        anim.setDuration(ms)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InCubic)
        anim.finished.connect(lambda: (
            widget.setVisible(False),
            widget.setGraphicsEffect(None),
        ))
        anim.start()
        widget.setProperty("_anim", anim)

    def _animate_progress(self, target: int):
        """Smoothly glide the progress bar value."""
        if self._prog_anim is not None:
            self._prog_anim.stop()
        self._prog_anim = QPropertyAnimation(self.progress_bar, b"value")
        self._prog_anim.setDuration(260)
        self._prog_anim.setStartValue(self.progress_bar.value())
        self._prog_anim.setEndValue(target)
        self._prog_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._prog_anim.start()

    # ── Helpers ───────────────────────────────────────────────────
    def _cleanup_thread_refs(self):
        self.thread = None
        self.worker = None

    def _set_controls_enabled(self, enabled: bool):
        self.drop_box.set_drops_enabled(enabled)
        self.setAcceptDrops(enabled)
        self.pick_btn.setEnabled(enabled)
        self.out_btn.setEnabled(enabled)
        self.rb_vocals.setEnabled(enabled)
        self.rb_full.setEnabled(enabled)
        self.rb_quick.setEnabled(enabled)
        self.rb_quality.setEnabled(enabled)

    def _effective_output(self) -> str:
        if self.custom_output:
            return self.custom_output
        if self.input_file:
            return str(Path(self.input_file).parent)
        return str(Path.home())

    # ── Settings ──────────────────────────────────────────────────
    def _restore_settings(self):
        saved = self.settings.value("output_folder", None)
        if saved and os.path.isdir(saved):
            self.custom_output = saved
            self.out_label.setText(f"Output: {saved}")

    def _save_settings(self):
        if self.custom_output:
            self.settings.setValue("output_folder", self.custom_output)

    # ── Validation ────────────────────────────────────────────────
    def _validate_input(self, path: str) -> bool:
        if not path or not os.path.exists(path):
            self._msg("File Not Found", "The selected file does not exist.", QMessageBox.Warning)
            return False
        if not os.access(path, os.R_OK):
            self._msg("Permission Denied", "Cannot read the selected file.", QMessageBox.Warning)
            return False
        return True

    def _validate_output(self, folder: str) -> bool:
        if not os.path.exists(folder):
            try:
                os.makedirs(folder, exist_ok=True)
            except OSError as exc:
                self._msg("Cannot Create Folder", str(exc), QMessageBox.Critical)
                return False
        if not os.access(folder, os.W_OK):
            self._msg("Permission Denied", "Cannot write to output folder.", QMessageBox.Warning)
            return False
        return True

    def _msg(self, title: str, text: str, icon=QMessageBox.Information):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon(icon)
        box.exec()

    # ── File / folder pickers ─────────────────────────────────────
    def pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio or Video File", "",
            "Media Files (*.wav *.mp3 *.flac *.aac *.ogg *.m4a "
            "*.mp4 *.mkv *.mov *.avi *.webm)",
        )
        if path:
            self.handle_selected_file(path)

    def pick_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder and self._validate_output(folder):
            self.custom_output = folder
            self.out_label.setText(f"Output: {folder}")
            self._save_settings()

    def handle_selected_file(self, path: str):
        if not path.lower().endswith(self.ALLOWED_EXT):
            self._msg(
                "Unsupported File",
                "Please select a supported audio or video file.",
                QMessageBox.Warning,
            )
            return
        if not self._validate_input(path):
            self.drop_box.clear()
            return

        self.input_file = path
        self.drop_box.set_filled(path)
        self.run_btn.setEnabled(True)
        logger.info("File selected: %s", path)
        self.out_label.setText(f"Output: {self._effective_output()}")

    # ── Processing ────────────────────────────────────────────────
    def cancel_processing(self):
        if self.worker:
            self.cancel_btn.setEnabled(False)
            self.status_label.setVisible(True)
            self.status_label.setText("Cancelling…")
            self.worker.cancel()

    def run_engine(self):
        if self.is_processing:
            self._msg("Processing", "Already processing — please wait.")
            return

        if not self.input_file or not os.path.exists(self.input_file):
            self._msg("File Missing", "The selected file is no longer available.", QMessageBox.Critical)
            self.drop_box.clear()
            self.input_file = None
            self.run_btn.setEnabled(False)
            return

        output_dir = self._effective_output()
        if not self._validate_output(output_dir):
            return

        # Show progress bar and status label with window grow animation
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("")
        self.progress_bar.setVisible(True)
        self.status_label.setText("Starting separation…")
        self.status_label.setStyleSheet("")
        self.status_label.setVisible(True)
        self.setFixedSize(300, 600)  # Grow to show progress bar and avoid squishing

        # Lock UI
        self._set_controls_enabled(False)
        self.run_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self.cancel_btn.setEnabled(True)
        self.is_processing = True

        mode    = "vocals" if self.rb_vocals.isChecked() else "full"
        quality = "quality" if self.rb_quality.isChecked() else "quick"

        # Tear down lingering thread
        if self.thread and self.thread.isRunning():
            try:
                if self.worker:
                    self.worker.cancel()
                self.thread.quit()
                self.thread.wait(2000)
            except Exception:
                pass

        self.thread = QThread()
        self.worker = EngineWorker(self.input_file, output_dir, mode, quality)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._cleanup_thread_refs)

        self.thread.start()
        logger.info("Processing started: mode=%s quality=%s", mode, quality)

    def _on_progress(self, pct: int, text: str):
        self._animate_progress(pct)
        self.status_label.setText(text)

    def _on_finished(self, stems: list, success: bool, error_msg: str):
        try:
            self.is_processing = False
            self._set_controls_enabled(True)
            self.run_btn.setVisible(True)
            self.run_btn.setEnabled(False)
            self.cancel_btn.setVisible(False)
            self.drop_box.clear()
            self.input_file = None

            if success:
                self._animate_progress(100)
                self.progress_bar.setStyleSheet(
                    f"QProgressBar::chunk {{ background: {_GREEN}; border-radius: 5px; }}"
                )
                QTimer.singleShot(1200, self._reset_bar_style)

                n = len(stems)
                self.status_label.setText(
                    f"Done — {n} stem{'s' if n != 1 else ''} saved"
                )
                self.status_label.setStyleSheet(
                    f"color: {_GREEN}; font-weight: 600; "
                    f"background: {_GREEN_BG}; border-radius: 4px;"
                )
                self.model_loaded_once = True
                logger.info("Completed — %d stems", n)
            else:
                self.status_label.setText(error_msg)
                self.status_label.setStyleSheet(
                    f"color: {_RED}; "
                    f"background: {_RED_BG}; border-radius: 4px;"
                )
                logger.error("Failed: %s", error_msg)

            # Hide progress bar and status label after a short delay
            QTimer.singleShot(1800, self._hide_progress_and_status)

            self.out_label.setText(f"Output: {self._effective_output()}")
            self._save_settings()
        except Exception as exc:
            logger.error("Error in _on_finished: %s", exc)

    def _reset_bar_style(self):
        self.progress_bar.setStyleSheet("")

    def _hide_progress_and_status(self):
        if not self.is_processing:
            self.progress_bar.setVisible(False)
            self.status_label.setVisible(False)
            self.setFixedSize(300, 520)  # Shrink back to idle size

    # ── Window events ─────────────────────────────────────────────
    def closeEvent(self, event):
        if self.is_processing:
            self.cancel_processing()
            if self.thread and self.thread.isRunning():
                self.thread.quit()
                self.thread.wait(3000)
        super().closeEvent(event)
