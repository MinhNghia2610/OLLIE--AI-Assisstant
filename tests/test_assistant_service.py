import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.assistant_service import OllieAssistant


class FakeMouth:
    def __init__(self):
        self.spoken = []

    def speak(self, text):
        self.spoken.append(text)


class FakeBrain:
    def think(self, text):
        return f"AI:{text}"


class FakeSkills:
    def __init__(self):
        self.stopped = False

    def _scan_music(self):
        return []

    def stop_music(self):
        self.stopped = True
        return "Đã tắt nhạc."

    def play_music(self, song_index=None):
        return f"Đang phát bài: {song_index}"

    def get_weather(self, city):
        return f"Thời tiết tại {city}"


class AssistantServiceTests(unittest.TestCase):
    def setUp(self):
        self.settings = SimpleNamespace(
            gemini_api_key="demo",
            weather_api_key="weather",
            model_name="gemini-2.5-flash",
            request_timeout=10,
            music_dir="/tmp/music",
        )
        self.mouth = FakeMouth()
        self.skills = FakeSkills()

    def build_assistant(self):
        return OllieAssistant(
            self.settings,
            brain=FakeBrain(),
            skills=self.skills,
            mouth=self.mouth,
        )

    def test_process_chat_uses_brain(self):
        assistant = self.build_assistant()
        reply = assistant.process_text("xin chao")
        self.assertEqual(reply.reply_text, "AI:xin chao")
        self.assertEqual(reply.intent, "chat")

    @patch("core.assistant_service.pygame.mixer.get_init", return_value=True)
    def test_process_play_music_uses_skills(self, _mock_get_init):
        assistant = self.build_assistant()
        reply = assistant.process_text("bật nhạc bài 3")
        self.assertEqual(reply.reply_text, "Đang phát bài: 3")
        self.assertEqual(reply.intent, "play_music")

    def test_process_exit_returns_should_exit(self):
        assistant = self.build_assistant()
        reply = assistant.process_text("tạm biệt")
        self.assertTrue(reply.should_exit)
        self.assertIsNone(reply.status_text)

    def test_process_can_speak_reply(self):
        assistant = self.build_assistant()
        assistant.process_text("thời tiết tại hà nội", speak_response=True)
        self.assertEqual(self.mouth.spoken[-1], "Thời tiết tại Hà Nội")


if __name__ == "__main__":
    unittest.main()
