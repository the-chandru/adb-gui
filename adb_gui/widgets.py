# adb_gui/widgets.py

"""
widgets.py

Custom PyQt5 widgets used by the ADB-GUI application.

Includes:
- DragDropListWidget: QListWidget subclass to support accepting dragged files/folders,
  enabling drag-and-drop upload to the connected Android device.

This module centralizes widget subclasses and helps keep main.py concise.
"""

from PyQt5.QtWidgets import QListWidget
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent


class DragDropListWidget(QListWidget):
    """
    QListWidget subclass that accepts dragged local files/folders from the OS file manager.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Accept drag enter events if dragged data contains local file URLs.
        """
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.isLocalFile() for url in urls):
                event.setDropAction(Qt.CopyAction)
                event.accept()
                return
        event.ignore()

    def dragMoveEvent(self, event):
        """
        Accept drag move events if conditions match drag enter.
        """
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.isLocalFile() for url in urls):
                event.setDropAction(Qt.CopyAction)
                event.accept()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        """
        Emits a signal or calls a handler upon drop, passing local file paths.

        Actual push/upload logic should be handled by the parent widget or main app.
        """
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        urls = event.mimeData().urls()
        local_paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        # For debugging or logging dropped paths (remove or modify as needed)
        for path in local_paths:
            print(f"Dropped local file/folder: {path}")
        # Accept the event so the default drop visual feedback is correct
        event.accept()

        # Ideally emit a signal or call a callback here to notify main app
        # Since signals are PyQt advanced topic, main app can subclass or assign method dynamically
        # e.g., self.parent().handle_files_dropped(local_paths)
        # Placeholder: print or use custom handler
        try:
            # If there is a handler attribute set externally
            if hasattr(self, 'files_dropped_handler'):
                self.files_dropped_handler(local_paths)
        except Exception as e:
            print(f"Error in files_dropped_handler: {e}")
