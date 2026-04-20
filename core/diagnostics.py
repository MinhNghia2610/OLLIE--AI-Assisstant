import platform
import shutil
from pathlib import Path

import pygame
import pyaudio

from config import Settings, get_settings
from core.hearing import Ear


def collect_runtime_diagnostics(settings: Settings | None = None) -> dict[str, object]:
    active_settings = settings or get_settings()
    ear = Ear()
    music_ready, music_message = _check_music_output()

    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "gemini_key": bool(active_settings.gemini_api_key),
        "weather_key": bool(active_settings.weather_api_key),
        "model_name": active_settings.model_name,
        "timeout": active_settings.request_timeout,
        "music_dir": active_settings.music_dir,
        "music_files": len(list(Path(active_settings.music_dir).glob("*.mp3"))),
        "flac_path": shutil.which("flac"),
        "say_path": shutil.which("say"),
        "audio_mode": "Default laptop microphone and speakers",
        "ear_available": ear.is_available,
        "ear_startup_message": ear.startup_message,
        "ear_error": ear.error_message,
        "ear_error_details": ear.error_details,
        "music_output_ready": music_ready,
        "music_output_message": music_message,
    }


def format_runtime_diagnostics(diagnostics: dict[str, object]) -> str:
    lines = [
        "=== System ===",
        f"Platform: {diagnostics['platform']}",
        f"Python: {diagnostics['python']}",
        "",
        "=== Config ===",
        f"GEMINI_API_KEY: {_format_bool(diagnostics['gemini_key'])}",
        f"WEATHER_API_KEY: {_format_bool(diagnostics['weather_key'])}",
        f"GEMINI_MODEL: {diagnostics['model_name']}",
        f"REQUEST_TIMEOUT: {diagnostics['timeout']}",
        f"MUSIC_DIR: {diagnostics['music_dir']}",
        f"Music files: {diagnostics['music_files']}",
        f"Audio mode: {diagnostics['audio_mode']}",
        "",
        "=== Tools ===",
        f"flac: {diagnostics['flac_path'] or 'missing'}",
        f"say: {diagnostics['say_path'] or 'missing'}",
        "",
        "=== Microphone ===",
        f"Default microphone ready: {diagnostics['ear_available']}",
        f"Startup message: {diagnostics['ear_startup_message']}",
        f"Error: {diagnostics['ear_error']}",
        f"Error details: {diagnostics['ear_error_details']}",
        "",
        "=== Speakers ===",
        f"Music output ready: {diagnostics['music_output_ready']}",
        f"Music output message: {diagnostics['music_output_message']}",
    ]
    return "\n".join(lines)


def _check_music_output() -> tuple[bool, str]:
    if not _has_default_output_device():
        return False, "Khong tim thay loa mac dinh cua laptop."

    try:
        pygame.mixer.init()
        return True, "Khoi tao pygame.mixer thanh cong voi loa mac dinh."
    except pygame.error as e:
        return False, f"Khoi tao pygame.mixer that bai: {e}"
    finally:
        if pygame.mixer.get_init():
            pygame.mixer.quit()


def _has_default_output_device() -> bool:
    audio = pyaudio.PyAudio()
    try:
        audio.get_default_output_device_info()
        return True
    except OSError:
        return False
    finally:
        audio.terminate()


def _format_bool(value: object) -> str:
    return "set" if value else "missing"
