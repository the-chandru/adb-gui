# adb_gui/preview.py

"""
preview.py

Reusable preview widgets and helper functions for the ADB-GUI application.
Supports previewing images, text, video, audio, and PDFs
within a PyQt5 application (macOS, Windows, Linux).

Dependencies:
- PyQt5
- PyQt5.QtMultimedia
- PyMuPDF (imported as fitz) for rendering PDFs

Note: For video and audio, codecs and system support may be required
(macOS: should "just work", Windows/Linux: check GStreamer/ffmpeg backend).
"""

import os
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QTextEdit, QSizePolicy, QScrollArea
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

try:
    import fitz  # PyMuPDF for PDF rendering
    HAVE_FITZ = True
except ImportError:
    HAVE_FITZ = False

# --- File Type Detection ---

def is_image_file(fname):
    return any(fname.lower().endswith(x) for x in ('.png', '.jpg', '.jpeg', '.bmp', '.gif'))

def is_video_file(fname):
    return any(fname.lower().endswith(x) for x in ('.mp4', '.mov', '.avi', '.mkv', '.webm'))

def is_audio_file(fname):
    return any(fname.lower().endswith(x) for x in ('.mp3', '.m4a', '.aac', '.wav', '.flac', '.ogg'))

def is_pdf_file(fname):
    return fname.lower().endswith('.pdf')

def is_text_file(fname):
    return any(fname.lower().endswith(x) for x in ('.txt', '.py', '.log', '.md', '.json', '.xml', '.csv'))

# --- Preview Widgets ---

class ImagePreviewWidget(QWidget):
    """
    Shows a scaled image preview.
    """
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.pixmap = QPixmap(image_path)
        self.update_pixmap()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_pixmap()

    def update_pixmap(self):
        if not self.pixmap.isNull():
            scaled = self.pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(scaled)
        else:
            self.label.setText("Invalid Image")

class TextPreviewWidget(QWidget):
    """
    Shows up to 16,000 chars of a file as plain text.
    """
    def __init__(self, file_path):
        super().__init__()
        te = QTextEdit()
        te.setReadOnly(True)
        try:
            with open(file_path, encoding='utf-8', errors='replace') as f:
                text = f.read(16000)
        except Exception as e:
            text = f"Could not display text: {e}"
        te.setText(text)
        layout = QVBoxLayout(self)
        layout.addWidget(te)
        self.setLayout(layout)

class VideoPreviewWidget(QWidget):
    """
    Video player for local video files using QtMultimedia.
    """
    def __init__(self, video_path):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(400, 300)
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.video_widget)
        self.setLayout(self.layout)

        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(self.video_widget)
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
        self.player.play()
        self.video_widget.show()

class AudioPreviewWidget(QWidget):
    """
    Audio player for basic playback with filename label.
    """
    def __init__(self, audio_path):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel(os.path.basename(audio_path))
        label.setAlignment(Qt.AlignHCenter)
        player = QMediaPlayer(self)
        url = QUrl.fromLocalFile(audio_path)
        player.setMedia(QMediaContent(url))
        player.play()
        layout.addWidget(label)
        self.setLayout(layout)
        self.player = player

class PDFPreviewWidget(QWidget):
    """
    PDF preview as scrollable image(s) using PyMuPDF (fitz).
    Displays the first N pages as images, vertically scrollable.
    """
    def __init__(self, file_path, max_pages=10):
        super().__init__()
        layout = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(5, 5, 5, 5)

        if HAVE_FITZ:
            try:
                doc = fitz.open(file_path)
                pages = min(max_pages, doc.page_count)
                if pages == 0:
                    vbox.addWidget(QLabel("(Empty PDF)"))
                for i in range(pages):
                    page = doc.load_page(i)
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5,1.5))
                    img_data = pix.tobytes("ppm")
                    pm = QPixmap()
                    pm.loadFromData(img_data)
                    scaled = pm.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    label = QLabel()
                    label.setPixmap(scaled)
                    label.setAlignment(Qt.AlignCenter)
                    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                    vbox.addWidget(label)
            except Exception as e:
                vbox.addWidget(QLabel(f"PDF could not be rendered: {e}"))
        else:
            vbox.addWidget(QLabel("PDF Preview requires PyMuPDF (fitz)"))

        container.setLayout(vbox)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        self.setLayout(layout)

# --- Preview Factory ---

def create_preview_widget(file_path):
    """
    Detects file type by extension and returns an appropriate QWidget to preview it.
    """
    fname = os.path.basename(file_path)
    if is_image_file(fname):
        return ImagePreviewWidget(file_path)
    if is_video_file(fname):
        return VideoPreviewWidget(file_path)
    if is_audio_file(fname):
        return AudioPreviewWidget(file_path)
    if is_pdf_file(fname):
        return PDFPreviewWidget(file_path)
    if is_text_file(fname):
        return TextPreviewWidget(file_path)
    # If nothing matches: try text and fallback if needed
    try:
        with open(file_path, encoding='utf-8', errors='replace') as f:
            text = f.read(32000)
            if text.strip():
                return TextPreviewWidget(file_path)
    except Exception:
        pass
    # Fallback
    widget = QLabel("Cannot preview this file type.")
    widget.setAlignment(Qt.AlignCenter)
    return widget

