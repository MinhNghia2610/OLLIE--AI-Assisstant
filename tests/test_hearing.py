import unittest
from unittest.mock import patch

from core.hearing import Ear


class HearingTests(unittest.TestCase):
    @patch("core.hearing.sr.Microphone")
    def test_ear_uses_default_microphone(self, mock_microphone):
        ear = Ear()

        self.assertTrue(ear.is_available)
        self.assertEqual(ear.startup_message, "Đang dùng microphone mặc định của laptop.")
        self.assertEqual(ear.selected_device_name, "Default Microphone")
        mock_microphone.assert_called_once_with()

    @patch("core.hearing.sr.Microphone", side_effect=OSError("No Default Input Device Available"))
    def test_ear_marks_default_microphone_unavailable(self, _mock_microphone):
        ear = Ear()

        self.assertFalse(ear.is_available)
        self.assertIsNone(ear.microphone)
        self.assertIn("Không tìm thấy microphone mặc định.", ear.error_message)
        self.assertEqual(ear.error_details, "No Default Input Device Available")


if __name__ == "__main__":
    unittest.main()
