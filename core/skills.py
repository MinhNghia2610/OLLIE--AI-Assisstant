from pathlib import Path

import pygame
import requests


class Skills:
    def __init__(self, music_dir: Path, weather_api_key: str | None, request_timeout: int = 10):
        self.music_dir = Path(music_dir)
        self.weather_api_key = weather_api_key
        self.request_timeout = request_timeout
        self.music_dir.mkdir(parents=True, exist_ok=True)

    def _scan_music(self) -> list[Path]:
        return sorted(self.music_dir.glob("*.mp3"))

    def get_weather(self, city: str = "Ho Chi Minh City") -> str:
        if not self.weather_api_key:
            return "Bạn chưa cấu hình WEATHER_API_KEY trong file .env."

        try:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": city,
                    "appid": self.weather_api_key,
                    "units": "metric",
                    "lang": "vi",
                },
                timeout=self.request_timeout,
            )
            data = response.json()
        except requests.RequestException:
            return "Xin lỗi, tôi không thể kết nối tới máy chủ thời tiết lúc này."

        if str(data.get("cod")) != "200":
            return f"Không tìm thấy thông tin thời tiết cho {city}."

        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        return (
            f"Thời tiết tại {city} hiện tại đang {desc}, "
            f"nhiệt độ khoảng {temp} độ C và độ ẩm là {humidity}%."
        )

    def play_music(self, song_index: int | None = None) -> str:
        if not pygame.mixer.get_init():
            return "Hệ thống âm thanh chưa được khởi tạo."

        songs = self._scan_music()
        if not songs:
            return "Trong thư mục chưa có bài hát nào."

        if song_index is None:
            selected = songs[0]
        else:
            idx = song_index - 1
            if not 0 <= idx < len(songs):
                return f"Chỉ có {len(songs)} bài hát, vui lòng chọn lại."
            selected = songs[idx]

        try:
            pygame.mixer.music.load(str(selected))
            pygame.mixer.music.play()
            return f"Đang phát bài: {selected.name}"
        except Exception as e:
            return f"Có lỗi khi phát nhạc: {e}"

    def stop_music(self) -> str:
        if not pygame.mixer.get_init():
            return "Hệ thống âm thanh chưa được khởi tạo."

        pygame.mixer.music.stop()
        return "Đã tắt nhạc."
