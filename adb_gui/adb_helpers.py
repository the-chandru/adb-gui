# adb_gui/adb_helpers.py

"""
adb_helpers.py

Helper functions and classes for running adb commands and processing outputs.

Provides:
- Async command execution with callbacks
- Convenience for checking device state, listing remote directories
- Utility parsers for adb command output

Designed for use in PyQt/PySide GUI applications or CLI tools.

"""

import os
from PyQt5.QtCore import QProcess


class AdbRunner:
    """
    Utility class to run adb commands asynchronously using QProcess.

    Usage:
        runner = AdbRunner(adb_path='adb')
        runner.run(['devices'], callback=your_callback_function)

    Callback signature:
        def callback(stdout: str, stderr: str, finished: bool, exitCode: int, status: int): ...
    """

    def __init__(self, adb_path='adb', parent=None):
        """
        Initialize AdbRunner.

        :param adb_path: Path to adb executable or just 'adb' if in PATH.
        :param parent: Optional QObject parent for QProcess.
        """
        self.adb_path = adb_path
        self.process = None
        self.output_buffer = ''
        self.parent = parent

    def run(self, args, callback):
        """
        Start adb command asynchronously.

        :param args: List of arguments for adb (e.g., ['devices'])
        :param callback: Function to call on output and finish
        """
        if self.process:
            self.process.kill()
            self.process.deleteLater()

        self.output_buffer = ""
        self.process = QProcess(self.parent)
        self.process.readyReadStandardOutput.connect(lambda: self._read_output(callback))
        self.process.readyReadStandardError.connect(lambda: self._read_output(callback))
        self.process.finished.connect(lambda exitCode, status: self._finished(exitCode, status, callback))

        self.process.start(self.adb_path, args)

    def _read_output(self, callback):
        out_bytes = self.process.readAllStandardOutput().data()
        err_bytes = self.process.readAllStandardError().data()
        out = out_bytes.decode('utf-8', errors='replace')
        err = err_bytes.decode('utf-8', errors='replace')

        self.output_buffer += out + err

        if callback:
            callback(out, err, finished=False, exitCode=None, status=None)

    def _finished(self, exitCode, status, callback):
        if callback:
            callback(None, None, finished=True, exitCode=exitCode, status=status)

    @staticmethod
    def parse_connected_devices(adb_devices_output):
        """
        Given the output of 'adb devices', parse connected and offline devices.

        Returns a dict with keys:
            'connected': list of serial numbers connected
            'offline': list of serial numbers offline
        """
        connected = []
        offline = []
        lines = adb_devices_output.strip().splitlines()
        for line in lines:
            if line.strip() == '' or line.startswith('List of devices attached'):
                continue
            parts = line.split()
            if len(parts) == 2:
                serial, state = parts
                if state == 'device':
                    connected.append(serial)
                elif state == 'offline':
                    offline.append(serial)
        return {'connected': connected, 'offline': offline}

    @staticmethod
    def parse_ls_p_output(ls_output):
        """
        Parse output of `adb shell ls -p` to list directory entries.

        Entries ending with '/' are directories.

        Returns a list of dicts:
            [{'name': 'file1', 'is_dir': False}, {'name': 'folder1', 'is_dir': True}, ...]
        """
        lines = ls_output.strip().splitlines()
        entries = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            is_dir = line.endswith('/')
            name = line[:-1] if is_dir else line
            entries.append({'name': name, 'is_dir': is_dir})
        return entries

    @staticmethod
    def is_remote_path_directory(adb_runner, remote_path, callback):
        """
        Checks whether a remote path on device is a directory or a file.

        Calls adb shell with the test and calls `callback(result_str)` where result_str is 'dir' or 'file'.

        This method runs asynchronously via adb_runner; callback will be called later.

        :param adb_runner: AdbRunner instance to execute commands
        :param remote_path: Remote device path to test
        :param callback: Function to call with result string ('dir' or 'file')
        """

        def inner_callback(stdout, stderr, finished=False, exitCode=None, status=None):
            if finished:
                result = adb_runner.output_buffer.strip()
                print(f"DEBUG path check output: '{stdout}' (exitCode: {exitCode}) result : {result}")
                callback(result)

        cmd = ['shell', f'if [ -d "{remote_path}" ]; then echo dir; else echo file; fi']
        adb_runner.run(cmd, inner_callback)


# Example usage of AdbRunner (outside GUI):
if __name__ == '__main__':
    def print_devices(stdout, stderr, finished, exitCode, status):
        if finished:
            print('Command finished with output:')
            print(adb_runner.output_buffer)
            devices = AdbRunner.parse_connected_devices(adb_runner.output_buffer)
            print('Connected devices:', devices['connected'])
            print('Offline devices:', devices['offline'])

    adb_runner = AdbRunner()
    adb_runner.run(['devices'], print_devices)
