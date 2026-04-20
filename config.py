from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None
    weather_api_key: str | None
    model_name: str
    request_timeout: int
    music_dir: Path


def get_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        weather_api_key=os.getenv("WEATHER_API_KEY"),
        model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "10")),
        music_dir=BASE_DIR / "assets" / "music",
    )
