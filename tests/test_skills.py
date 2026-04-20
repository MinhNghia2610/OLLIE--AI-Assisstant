import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core.skills import Skills


class SkillsTests(unittest.TestCase):
    def test_get_weather_requires_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skills = Skills(Path(tmpdir), weather_api_key=None, request_timeout=3)
            self.assertEqual(
                skills.get_weather("Hanoi"),
                "Bạn chưa cấu hình WEATHER_API_KEY trong file .env.",
            )

    @patch("core.skills.requests.get")
    def test_get_weather_formats_response(self, mock_get: Mock):
        mock_response = Mock()
        mock_response.json.return_value = {
            "cod": 200,
            "weather": [{"description": "nắng đẹp"}],
            "main": {"temp": 31, "humidity": 65},
        }
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            skills = Skills(Path(tmpdir), weather_api_key="demo-key", request_timeout=7)
            message = skills.get_weather("Hanoi")

        self.assertIn("Thời tiết tại Hanoi hiện tại đang nắng đẹp", message)
        self.assertIn("31 độ C", message)
        self.assertIn("65%", message)
        mock_get.assert_called_once()

    @patch("core.skills.pygame.mixer.get_init", return_value=False)
    def test_play_music_requires_initialized_audio(self, _mock_get_init: Mock):
        with tempfile.TemporaryDirectory() as tmpdir:
            skills = Skills(Path(tmpdir), weather_api_key="demo-key")
            self.assertEqual(
                skills.play_music(),
                "Hệ thống âm thanh chưa được khởi tạo.",
            )

    @patch("core.skills.pygame.mixer.get_init", return_value=True)
    def test_play_music_reports_empty_library(self, _mock_get_init: Mock):
        with tempfile.TemporaryDirectory() as tmpdir:
            skills = Skills(Path(tmpdir), weather_api_key="demo-key")
            self.assertEqual(
                skills.play_music(),
                "Trong thư mục chưa có bài hát nào.",
            )

    @patch("core.skills.pygame.mixer.get_init", return_value=True)
    def test_play_music_rejects_invalid_index(self, _mock_get_init: Mock):
        with tempfile.TemporaryDirectory() as tmpdir:
            music_dir = Path(tmpdir)
            (music_dir / "Bai_Hat_1.mp3").write_bytes(b"demo")
            skills = Skills(music_dir, weather_api_key="demo-key")

            self.assertEqual(
                skills.play_music(song_index=2),
                "Chỉ có 1 bài hát, vui lòng chọn lại.",
            )


if __name__ == "__main__":
    unittest.main()
