# Spleet — Offline Stem Splitter

A lightweight desktop app that splits any audio or video file into individual stems (vocals, drums, bass, other) using [Demucs](https://github.com/facebookresearch/demucs). Runs **100 % offline** — no internet required after installation.

![Spleet screenshot](shared/assets/logo.png)

---

## Features

- **Drag-and-drop** or browse for audio / video files
- **2-stem mode** — vocals + accompaniment
- **4-stem mode** — vocals, drums, bass, other
- **Quick** (htdemucs) or **Quality** (htdemucs_ft) models
- Modern dark-themed UI
- Works entirely offline with bundled models

## Supported Formats

`.wav` `.mp3` `.flac` `.aac` `.ogg` `.m4a` `.mp4` `.mkv` `.mov` `.avi` `.webm`

---

## Development Setup

### Prerequisites

- Python 3.10 – 3.12 (3.11 recommended)
- pip

### Install dependencies

```bash
pip install -r shared/requirements.txt
```

### Run in development mode

```bash
# Windows
python windows/app.py

# macOS
python mac/app.py

# Linux
python linux/app.py
```

---

## Building the Installer

### 1. Build platform artifact with PyInstaller

#### Windows

```bash
cd windows
pip install -r requirements.txt
pyinstaller Spleet.spec --noconfirm
```

This creates `windows/dist/Spleet/` containing the portable app.

#### macOS

```bash
cd mac
pip install -r requirements.txt
pyinstaller Spleet.spec --noconfirm
```

This creates `mac/dist/Spleet.app`.

#### Linux

```bash
cd linux
pip install -r requirements.txt
pyinstaller Spleet.spec --noconfirm
```

This creates `linux/dist/Spleet/`.

### 2. Test the portable build

```bash
windows\dist\Spleet\Spleet.exe
```

### 3. Create the Windows installer

1. Install **[Inno Setup](https://jrsoftware.org/isinfo.php)** (free).
2. Open `windows/installer.iss` in the Inno Setup Compiler.
3. Click **Build → Compile** (or press Ctrl+F9).
4. The installer is written to the `windows/Output/` folder:
   ```
  windows\Output\Spleet_Setup_0.2.0.exe
   ```

You can also build from the command line if `iscc` is on your PATH:

```bash
cd windows
iscc installer.iss
```

### 4. Distribute

Ship the single `Spleet_Setup_0.2.0.exe` file. Users double-click it, choose an install location, and they're done.

---

## Project Structure

```
shared/
  engine/
    audio_engine.py     Builds the Demucs subprocess command
  ui/
    main_window.py      PySide6 main window with dark theme
    worker.py           QThread worker that streams Demucs progress
  models/
    hub/checkpoints/    Bundled Demucs model weights
  assets/
    logo.png / logo.ico App icons
  requirements.txt      Shared runtime dependencies
windows/
  app.py                Windows entry point
  Spleet.spec           Windows PyInstaller spec
  installer.iss         Inno Setup installer script
  requirements.txt      Windows build requirements
mac/
  app.py                macOS entry point
  Spleet.spec           macOS PyInstaller spec (.app bundle)
  requirements.txt      macOS build requirements
linux/
  app.py                Linux entry point
  Spleet.spec           Linux PyInstaller spec
  requirements.txt      Linux build requirements
.github/workflows/
  build.yml             Matrix CI build for Windows/macOS/Linux
```

---

## License

MIT
