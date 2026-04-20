from pathlib import Path

from dotenv import dotenv_values

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT_DIR / ".env"
KNOWN_ENV_KEYS = (
    "GEMINI_API_KEY",
    "WEATHER_API_KEY",
    "GEMINI_MODEL",
    "REQUEST_TIMEOUT",
)
LEGACY_ENV_KEYS = ("MIC_DEVICE_INDEX",)


def load_env_settings(env_path: Path | None = None) -> dict[str, str]:
    path = env_path or ENV_FILE
    values = dotenv_values(path)
    return {
        key: "" if values.get(key) is None else str(values.get(key))
        for key in KNOWN_ENV_KEYS
    }


def save_env_settings(updates: dict[str, str], env_path: Path | None = None) -> Path:
    path = env_path or ENV_FILE
    current = {
        str(key): "" if value is None else str(value)
        for key, value in dotenv_values(path).items()
    }

    for legacy_key in LEGACY_ENV_KEYS:
        current.pop(legacy_key, None)

    for key, value in updates.items():
        current[key] = value.strip()

    ordered_keys = list(KNOWN_ENV_KEYS) + sorted(key for key in current if key not in KNOWN_ENV_KEYS)
    lines = [f"{key}={_format_env_value(current.get(key, ''))}" for key in ordered_keys]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def _format_env_value(value: str) -> str:
    if not value:
        return ""

    if any(char.isspace() for char in value) or "#" in value:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    return value
