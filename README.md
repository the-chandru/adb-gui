# adb-gui

**adb-gui** is a graphical user interface (GUI) built with Python and PyQt5 to manage Android devices via ADB (Android Debug Bridge). It provides a Finder/Explorer-like experience for browsing, previewing, and transferring files on Android devices, all without command-line use.

## Features

- **Remote File Browser:** Easily navigate your Android device's file system.
- **Drag & Drop Support:** Upload files/folders by dragging them onto the app.
- **Bulk Upload/Download:** Select multiple files/folders for batch transfers.
- **Progress Bar & Status:** Real-time transfer progress and device status display.
- **File Previews:**  
  - Images (png, jpg, bmp, gif, etc.)  
  - Text (txt, json, logs, code, etc.)  
  - Videos (mp4, mov, avi, mkv) with in-app playback  
  - Audio (mp3, aac, wav, flac) with in-app playback  
  - PDFs with first-page rendering (via PyMuPDF)
- **Manual Push/Pull:** Enter custom paths for targeted transfers.
- **Detailed Logging:** Console panel with full adb output and any errors.
- **Cross-Platform:** Works on macOS, Linux, and Windows.

## Requirements

- Python 3.7+
- Android Debug Bridge (adb) in your PATH
- PyQt5
- PyMuPDF (for PDF preview; optional)

## Installation & Setup

**Clone the repository**
```bash
git clone https://github.com/the-chandru/adb-gui.git
cd adb-gui
```

**One-click setup and launch**
```bash
./run_adb_gui.sh
```
This script uses or creates a `.venv` virtual environment, installs all dependencies, and launches the app.

**Manual setup**
1. Create and activate a virtual environment:
    - Linux/macOS:
      ```bash
      python3 -m venv .venv
      source .venv/bin/activate
      ```
    - Windows:
      ```bat
      python -m venv .venv
      .\.venv\Scripts\activate
      ```
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Run the app:
    ```bash
    python -m adb_gui.main
    ```

## Usage

- On startup, your device is checked and the default folder opens (`/sdcard`).
- Browse folders/files; double-click folders to enter them.
- Drag files/folders from Finder/Explorer into the app to upload.
- Preview images, text, video, audio, or PDFs directly in the app.
- Use manual entry fields to perform custom `adb push` or `pull`.
- Monitor operation progress and logs in the UI panels.

## Project Structure

```text
adb-gui/
  ├── adb_gui/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── widgets.py
  │   ├── preview.py
  │   ├── adb_helpers.py
  ├── tests/
  │   ├── __init__.py
  │   ├── test_adb_helpers.py
  │   ├── test_preview.py
  ├── requirements.txt
  ├── run_adb_gui.sh
  ├── README.md
  ├── LICENSE
```

## Testing

Run all tests:
```bash
python -m unittest discover
```

## Troubleshooting

- Verify `adb` is installed and in your PATH.
- Install system media libraries if video/audio playback does not work.
- Install PyMuPDF (`pip install PyMuPDF`) for PDF preview support.


## No Warranty

> THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.  
> See LICENSE for details.


## License

MIT — See [LICENSE](LICENSE) for full terms.


## Contributions

Pull requests and issue reports are welcome!


## Contact

CC / the-chandru  

Thank you for using **adb-gui**!
