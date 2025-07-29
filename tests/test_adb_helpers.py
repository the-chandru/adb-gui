import unittest
from adb_gui.adb_helpers import AdbRunner

class TestAdbHelpers(unittest.TestCase):
    def test_parse_connected_devices(self):
        sample = """List of devices attached
emulator-5554	device
123456789ABCDEF	offline
"""
        parsed = AdbRunner.parse_connected_devices(sample)
        self.assertEqual(parsed['connected'], ['emulator-5554'])
        self.assertEqual(parsed['offline'], ['123456789ABCDEF'])

    def test_parse_ls_p_output(self):
        ls_output = "folder1/\nfile1.txt\n"
        entries = AdbRunner.parse_ls_p_output(ls_output)
        self.assertEqual(entries, [
            {'name': 'folder1', 'is_dir': True},
            {'name': 'file1.txt', 'is_dir': False}
        ])

if __name__ == '__main__':
    unittest.main()
