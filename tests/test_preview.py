import unittest
from adb_gui import preview

class TestPreviewHelpers(unittest.TestCase):
    def test_is_video_file(self):
        self.assertTrue(preview.is_video_file('movie.mp4'))
        self.assertFalse(preview.is_video_file('image.png'))

    def test_is_pdf_file(self):
        self.assertTrue(preview.is_pdf_file('manual.pdf'))
        self.assertFalse(preview.is_pdf_file('notes.txt'))

    def test_is_audio_file(self):
        self.assertTrue(preview.is_audio_file('track.mp3'))
        self.assertFalse(preview.is_audio_file('file.mov'))

    def test_is_image_file(self):
        self.assertTrue(preview.is_image_file('pic.jpeg'))
        self.assertFalse(preview.is_image_file('main.py'))

if __name__ == '__main__':
    unittest.main()
