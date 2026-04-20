import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pygame

import main


class MainHelpersTests(unittest.TestCase):
    @patch("main.pygame.mixer.init")
    def test_initialize_audio_returns_true_when_mixer_starts(self, mock_init):
        self.assertTrue(main.initialize_audio())
        mock_init.assert_called_once_with()

    @patch("main.pygame.mixer.init", side_effect=pygame.error("audio failed"))
    def test_initialize_audio_returns_false_when_mixer_fails(self, _mock_init):
        self.assertFalse(main.initialize_audio())

    @patch("builtins.input", return_value="  Bật nhạc bài 3  ")
    def test_read_text_command_normalizes_keyboard_input(self, _mock_input):
        self.assertEqual(main.read_text_command(), "bật nhạc bài 3")

    @patch("builtins.input", side_effect=EOFError)
    def test_read_text_command_converts_eof_into_exit_command(self, _mock_input):
        self.assertEqual(main.read_text_command(), "tạm biệt")


class MainFlowTests(unittest.TestCase):
    def test_main_falls_back_to_keyboard_when_microphone_is_missing(self):
        events = []

        class FakeEar:
            def __init__(self):
                self.is_available = False
                self.error_message = "Không tìm thấy microphone mặc định."
                self.error_details = "No Default Input Device Available"
                self.startup_message = None

        class FakeMouth:
            def speak(self, text):
                events.append(("speak", text))

        class FakeAssistant:
            def __init__(self, _settings):
                self.mouth = FakeMouth()

            def process_text(self, text, speak_response=False):
                events.append(("process_text", text, speak_response))
                if text == "bật nhạc bài 2":
                    reply = SimpleNamespace(
                        reply_text="Đang phát bài 2",
                        status_text="Đang phát bài 2",
                        should_exit=False,
                    )
                else:
                    reply = SimpleNamespace(
                    reply_text="Tạm biệt bạn, hẹn gặp lại!",
                    status_text=None,
                    should_exit=True,
                )
                if speak_response:
                    self.mouth.speak(reply.reply_text)
                return reply

        keyboard_inputs = iter(["bật nhạc bài 2", "tạm biệt"])

        with patch.object(
            main,
            "get_settings",
            return_value=SimpleNamespace(
                gemini_api_key="demo-key",
                weather_api_key="weather-key",
                model_name="gemini-2.5-flash",
                request_timeout=10,
                music_dir="/tmp/music",
            ),
        ), patch.object(main, "initialize_audio", return_value=True), patch.object(main, "Ear", FakeEar), patch.object(
            main, "OllieAssistant", FakeAssistant
        ), patch.object(main, "read_text_command", side_effect=lambda: next(keyboard_inputs)
        ):
            main.run_cli()

        self.assertIn(("process_text", "bật nhạc bài 2", True), events)
        self.assertIn(("process_text", "tạm biệt", True), events)
        self.assertIn(("speak", "Tạm biệt bạn, hẹn gặp lại!"), events)


if __name__ == "__main__":
    unittest.main()
