import unittest

from core.commands import extract_city, extract_song_index, parse_rule_command


class CommandParsingTests(unittest.TestCase):
    def test_extract_song_index_from_music_command(self):
        self.assertEqual(extract_song_index("bat nhac bai 3"), 3)

    def test_extract_song_index_returns_none_when_missing(self):
        self.assertIsNone(extract_song_index("bat nhac di"))

    def test_extract_city_from_weather_phrase(self):
        self.assertEqual(extract_city("thời tiết ở hà nội"), "Hà Nội")

    def test_extract_city_defaults_to_hanoi(self):
        self.assertEqual(extract_city("thời tiết hôm nay"), "Hanoi")

    def test_parse_play_music_command(self):
        self.assertEqual(
            parse_rule_command("Bật nhạc bài 2"),
            {"intent": "play_music", "song_index": 2},
        )

    def test_parse_stop_music_command(self):
        self.assertEqual(
            parse_rule_command("Ngừng nhạc nhé"),
            {"intent": "stop_music"},
        )

    def test_parse_weather_command(self):
        self.assertEqual(
            parse_rule_command("Thời tiết tại đà nẵng thế nào"),
            {"intent": "weather", "city": "Đà Nẵng"},
        )

    def test_parse_unknown_command_returns_none(self):
        self.assertIsNone(parse_rule_command("kể cho mình một câu chuyện"))


if __name__ == "__main__":
    unittest.main()
