# adb_gui/main.py

"""
main.py

Main entry point and primary GUI application class for ADB-GUI.

Combines:
- ADB interaction (via adb_helpers)
- UI widgets (from widgets.py)
- File previews (from preview.py)
- Full-featured remote file browser
- Drag-drop upload support
- Progress bar for transfers
- Status and console log

To run the app, execute this module directly.
"""

import sys
import os
import tempfile

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QTextEdit, QLabel, QLineEdit,
    QListWidget, QMessageBox, QSplitter, QSizePolicy, QProgressBar
)
from PyQt5.QtGui import QPixmap, QDragEnterEvent, QDropEvent
from PyQt5.QtCore import Qt, QTimer

from adb_gui.widgets import DragDropListWidget
from adb_gui.adb_helpers import AdbRunner
from adb_gui.preview import create_preview_widget


class ADBGui(QWidget):
    """
    Main Window class integrating all components for the ADB GUI app.
    """

    def __init__(self):
        super().__init__()

        # Path to adb binary; update if adb is not in system PATH
        self.adb_path = 'adb'

        # Current remote directory path shown in browser
        self.remote_cwd = '/'

        # Buffer for ADB command output accumulation
        self.output_buffer = ""

        # QProcess wrapper handled by AdbRunner
        self.adb_runner = AdbRunner(self.adb_path, parent=self)

        # List to store temporary preview filepaths to clean up later
        self.temp_preview_files = set()

        # Setup UI
        self.initUI()

        # Initialize: check device and load remote directory
        self.check_device()
        self.load_remote_directory(self.remote_cwd)

    def initUI(self):
        self.setWindowTitle('ADB GUI with File Browser, Preview & Drag-Drop')
        self.setGeometry(100, 100, 900, 600)
        main_layout = QVBoxLayout()

        # -- Top Controls --
        top_layout = QHBoxLayout()
        self.device_label = QLabel('Device Status: Unknown')
        top_layout.addWidget(self.device_label)

        self.check_device_btn = QPushButton('Check Device')
        self.check_device_btn.clicked.connect(self.check_device)
        top_layout.addWidget(self.check_device_btn)

        self.restart_adb_btn = QPushButton('Restart ADB Server')
        self.restart_adb_btn.clicked.connect(self.restart_adb_server)
        top_layout.addWidget(self.restart_adb_btn)

        main_layout.addLayout(top_layout)

        # -- Path Inputs --
        path_layout = QHBoxLayout()

        self.remote_path_input = QLineEdit()
        self.remote_path_input.setPlaceholderText('Remote Path on Device')
        path_layout.addWidget(self.remote_path_input)

        self.local_path_input = QLineEdit()
        self.local_path_input.setPlaceholderText('Local Path on this computer')
        path_layout.addWidget(self.local_path_input)

        browse_local_btn = QPushButton('Browse Local')
        browse_local_btn.clicked.connect(self.browse_local_path)
        path_layout.addWidget(browse_local_btn)

        main_layout.addLayout(path_layout)

        # -- Pull and Push buttons --
        hand_buttons_layout = QHBoxLayout()
        self.pull_btn = QPushButton('ADB Pull (Download)')
        self.pull_btn.clicked.connect(self.adb_pull_manual)
        hand_buttons_layout.addWidget(self.pull_btn)

        self.push_btn = QPushButton('ADB Push (Upload)')
        self.push_btn.clicked.connect(self.adb_push_manual)
        hand_buttons_layout.addWidget(self.push_btn)

        main_layout.addLayout(hand_buttons_layout)

        # -- Splitter for remote browser and previews/log --
        splitter = QSplitter()

        # -- Remote file list with drag/drop --
        self.remote_file_list = DragDropListWidget()
        self.remote_file_list.setAcceptDrops(True)
        self.remote_file_list.setDragEnabled(True)
        self.remote_file_list.viewport().setAcceptDrops(True)

        # Connect drag/drop events to handlers
        self.remote_file_list.dragEnterEvent = self.remote_drag_enter_event
        self.remote_file_list.dropEvent = self.remote_drop_event
        self.remote_file_list.viewport().dragEnterEvent = self.remote_drag_enter_event
        self.remote_file_list.viewport().dropEvent = self.remote_drop_event

        self.remote_file_list.itemDoubleClicked.connect(self.remote_item_double_clicked)
        self.remote_file_list.setSelectionMode(QListWidget.SingleSelection)

        splitter.addWidget(self.remote_file_list)

        # -- Right Pane: preview, download & console log --
        right_pane = QWidget()
        right_layout = QVBoxLayout()

        # Container for preview widget(s)
        self.preview_container = QWidget()
        self.preview_container.setMinimumSize(400, 300)
        self.preview_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_container.setObjectName("previewContainer")
        self.preview_container.setStyleSheet("QWidget#previewContainer { border: 1px solid gray; border-radius: 5px;}")
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(5,5,5,5)
        self.preview_layout.setSpacing(0)
        self.preview_layout.setAlignment(Qt.AlignCenter)
        self.preview_label = QLabel('Preview Area')
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setWordWrap(True)
        self.preview_layout.addWidget(self.preview_label)
        right_layout.addWidget(self.preview_container)

        # Download selected file button
        self.download_btn = QPushButton('Download Selected File')
        self.download_btn.clicked.connect(self.download_selected_file)
        self.download_btn.setEnabled(False)
        right_layout.addWidget(self.download_btn)

        # Output console for logs
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        right_layout.addWidget(self.output_console)

        right_pane.setLayout(right_layout)
        splitter.addWidget(right_pane)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        # Navigation buttons: up directory and refresh
        nav_layout = QHBoxLayout()
        self.up_btn = QPushButton('Up Directory')
        self.up_btn.clicked.connect(self.browse_up)
        nav_layout.addWidget(self.up_btn)

        self.refresh_btn = QPushButton('Refresh')
        self.refresh_btn.clicked.connect(lambda: self.load_remote_directory(self.remote_cwd))
        nav_layout.addWidget(self.refresh_btn)

        main_layout.addLayout(nav_layout)

        # Progress bar hidden by default
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        self.setLayout(main_layout)

        # Connect selection changes in remote file list
        self.remote_file_list.itemSelectionChanged.connect(self.selection_changed)

    # === ADB Command Helpers ===

    def run_adb_command(self, args, callback=None):
        """
        Run adb command asynchronously, show indeterminate progress bar.
        The callback receives partial outputs and finish notification.
        """
        # if self.adb_runner.process:
        #     self.adb_runner.process.kill()
        # self.output_buffer = ""
        self.progress_bar.show()
        output_buffer = ""

        def wrapped_callback(stdout, stderr, finished=False, exitCode=None, status=None):
            nonlocal output_buffer
            if stdout:
                output_buffer += stdout
            if stderr:
                output_buffer += stderr
            if finished:
                self.progress_bar.hide()
                if callback:
                    callback(output_buffer, None, finished, exitCode, status)
            else:
                if callback:
                    callback(stdout, stderr, finished, None, None)

        self.adb_runner.run(args, wrapped_callback)

    # === Device Management ===

    def check_device(self):
        """
        Check connected devices and update UI.
        """
        def callback(stdout, stderr, finished=False, exitCode=None, status=None):
            if finished:
                devices = self.adb_runner.output_buffer
                devices_info = self.adb_runner.parse_connected_devices(devices)
                connected = devices_info['connected']
                offline = devices_info['offline']
                if connected:
                    text = f"Device Status: Connected: {', '.join(connected)}"
                    self.device_label.setText(text)
                    self.log_output(f"Device(s) connected: {', '.join(connected)}")
                elif offline:
                    self.device_label.setText(f"Device Status: Offline: {', '.join(offline)}")
                    self.log_output(f"Device(s) offline: {', '.join(offline)}")
                    self.show_offline_warning()
                else:
                    self.device_label.setText("Device Status: No devices connected")
                    self.log_output("No devices connected. Connect device and enable USB debugging.")

        self.run_adb_command(['devices'], callback)

    def show_offline_warning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Device Offline")
        msg.setText(
            "Your device is detected but currently 'offline'.\n\n"
            "Please check:\n"
            "- Unlock your Android device screen.\n"
            "- Revoke USB debugging authorizations in Developer options.\n"
            "- Reconnect USB cable and accept any debugging prompts.\n"
            "- Restart adb server if needed."
        )
        msg.exec_()

    def restart_adb_server(self):
        self.log_output("Restarting adb server...")
        def callback(stdout, stderr, finished=False, exitCode=None, status=None):
            if finished:
                self.log_output(self.output_buffer)
                self.check_device()
        self.run_adb_command(['kill-server'], callback=lambda *a: None)
        from PyQt5.QtCore import QProcess, QTimer
        QProcess().startDetached(self.adb_path, ['start-server'])
        # Slight delay before device check
        QTimer.singleShot(500, self.check_device)

    # === Remote File Browser ===

    def load_remote_directory(self, path):
        """
        Lists the contents of the remote directory and fills the file list.
        """
        self.log_output(f'Loading remote directory: {path}')
        def callback(stdout, stderr, finished=False, exitCode=None, status=None):
            if finished:
                if exitCode != 0:
                    self.log_output(f"Failed to list directory: {path}\nError: {self.output_buffer}")
                    return
                lines = stdout.strip().splitlines()
                self.remote_file_list.clear()
                if path != '/':
                    self.remote_file_list.addItem('../')
                for item in lines:
                    self.remote_file_list.addItem(item)
                self.remote_cwd = path
                self.remote_path_input.setText(path)
                self.log_output(f'Loaded directory: {path}')
                self.log_output(f'number of iles {self.remote_file_list.count()}')
                self.device_label.setText(f'Device Status: Connected. {len(lines)} item(s) in current folder.')
        self.run_adb_command(['shell', 'ls', '-p', path], callback)

    def remote_item_double_clicked(self, item):
        """
        Handle double click on remote file browser:
        if dir: open directory, else preview file.
        """
        name = item.text()
        if name == '../':
            self.browse_up()
            return
        full_path = os.path.join(self.remote_cwd, name.rstrip('/'))

        def after_check(result):
            if result == 'dir':
                QTimer.singleShot(0, lambda: self.load_remote_directory(full_path))
            else:  # default to preview file
                QTimer.singleShot(0, lambda: self.preview_remote_file(full_path))

        self.is_remote_directory(full_path, after_check)

    def browse_up(self):
        """
        Go up to parent directory.
        """
        if self.remote_cwd == '/':
            return
        parent = os.path.dirname(self.remote_cwd.rstrip('/'))
        if parent == '':
            parent = '/'
        self.load_remote_directory(parent)

    # === Preview Methods ===

    def preview_remote_file(self, remote_file):
        """
        Pull remote file locally and show appropriate preview widget.
        """
        self.log_output(f"Previewing file: {remote_file}")
        temp_dir = tempfile.gettempdir()
        local_temp_path = os.path.join(temp_dir, os.path.basename(remote_file))
        self.temp_preview_files.add(local_temp_path)

        def callback(stdout, stderr, finished=False, exitCode=None, status=None):
            if finished and exitCode == 0:
                self.clear_preview()
                preview_widget = create_preview_widget(local_temp_path)
                self._current_preview_widget = preview_widget  # Keep reference to prevent GC
                
                # Special handling if it is a video widget
                # from PyQt5.QtMultimediaWidgets import QVideoWidget
                # if isinstance(preview_widget, QVideoWidget):
                #     preview_widget.setMinimumSize(360, 240)
                #     preview_widget.show()
                
                self.preview_layout.addWidget(preview_widget)
            elif finished:
                self.clear_preview()
                self.preview_label.setText('Failed to load preview.')

        self.run_adb_command(['pull', remote_file, local_temp_path], callback)

    def clear_preview(self):
        # Remove all widgets from preview area and delete them safely
        while self.preview_layout.count():
            child = self.preview_layout.takeAt(0)
            widget = child.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        

    # === Drag and Drop Handlers ===

    def remote_drag_enter_event(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.setDropAction(Qt.CopyAction)
            event.acceptProposedAction()
        else:
            event.ignore()

    def remote_drop_event(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            event.ignore()
            return
        success_count = 0
        for url in urls:
            local_path = url.toLocalFile()
            if not local_path:
                continue
            remote_target = self.remote_cwd
            self.log_output(f"Pushing {local_path} to {remote_target}...")
            from subprocess import Popen, PIPE
            proc = Popen([self.adb_path, 'push', local_path, remote_target], stdout=PIPE, stderr=PIPE)
            out, err = proc.communicate()
            if proc.returncode == 0:
                self.log_output(f"Pushed {local_path} successfully.")
                success_count += 1
            else:
                self.log_output(f"Failed to push {local_path}: {err.decode()}")
        if success_count > 0:
            self.load_remote_directory(self.remote_cwd)
        event.acceptProposedAction()

    # === UI Selection Change ===

    def selection_changed(self):
        selected_items = self.remote_file_list.selectedItems()
        if not selected_items:
            self.download_btn.setEnabled(False)
            self.clear_preview()
            return
        name = selected_items[0].text()
        if name.endswith('/') or name == '../':
            self.download_btn.setEnabled(False)
            self.clear_preview()
            return
        self.download_btn.setEnabled(True)
        full_path = os.path.join(self.remote_cwd, name)
        self.preview_remote_file(full_path)

    # === Manual Pull/Push ===

    def download_selected_file(self):
        selected_items = self.remote_file_list.selectedItems()
        if not selected_items:
            return
        name = selected_items[0].text()
        if name.endswith('/') or name == '../':
            QMessageBox.information(self, "Download", "Please select a file to download (not a directory)")
            return
        remote_file = os.path.join(self.remote_cwd, name)
        save_path, _ = QFileDialog.getSaveFileName(self, "Save file as", name)
        if not save_path:
            return
        self.log_output(f"Downloading {remote_file} to {save_path}...")
        def callback(stdout, stderr, finished=False, exitCode=None, status=None):
            if finished:
                if exitCode == 0:
                    self.log_output("Download successful.")
                else:
                    self.log_output(f"Download failed: {self.output_buffer}")
        self.run_adb_command(['pull', remote_file, save_path], callback)

    def browse_local_path(self):
        path = QFileDialog.getExistingDirectory(self, 'Select Local Directory')
        if path:
            self.local_path_input.setText(path)

    def adb_pull_manual(self):
        remote = self.remote_path_input.text().strip()
        local = self.local_path_input.text().strip()
        if not remote or not local:
            self.log_output("Please specify both remote and local paths for pull.")
            return
        self.log_output(f"Running adb pull {remote} {local}...")
        def callback(stdout, stderr, finished=False, exitCode=None, status=None):
            if finished:
                if exitCode == 0:
                    self.log_output("Pull completed successfully.")
                else:
                    self.log_output(f"Pull failed: {self.output_buffer}")
        self.run_adb_command(['pull', remote, local], callback)

    def adb_push_manual(self):
        local = self.local_path_input.text().strip()
        remote = self.remote_path_input.text().strip()
        if not local or not remote:
            self.log_output("Please specify both local and remote paths for push.")
            return
        self.log_output(f"Running adb push {local} {remote}...")
        def callback(stdout, stderr, finished=False, exitCode=None, status=None):
            if finished:
                if exitCode == 0:
                    self.log_output("Push completed successfully.")
                    self.load_remote_directory(self.remote_cwd)
                else:
                    self.log_output(f"Push failed: {self.output_buffer}")
        self.run_adb_command(['push', local, remote], callback)

    # --- Utility Methods ---

    def is_remote_directory(self, remote_path, callback):
        """
        Checks if remote path is a directory or file, calls callback with 'dir' or 'file'.
        """
        self.adb_runner.is_remote_path_directory(self.adb_runner, remote_path, callback)

    def log_output(self, message):
        """
        Append message to the output console, also print to stdout for debug.
        """
        self.output_console.append(message)
        print(message)

    # --- Cleanup temp files on close ---

    def closeEvent(self, event):
        # Stop any active media player
        if hasattr(self, "_current_preview_widget") and self._current_preview_widget is not None:
            widget = self._current_preview_widget
            player = getattr(widget, "player", None)
            if player is not None:
                player.stop()
        for file in self.temp_preview_files:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except OSError:
                pass
        event.accept()


# --- Run Application ---

def main():
    app = QApplication(sys.argv)
    window = ADBGui()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
