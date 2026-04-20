import re


def extract_song_index(text: str) -> int | None:
    match = re.search(r"\b(\d+)\b", text)
    return int(match.group(1)) if match else None


def extract_city(text: str) -> str:
    lowered = text.lower().strip()

    for marker in (
        "thời tiết ở ",
        "thời tiết tại ",
        "dự báo thời tiết ở ",
        "dự báo thời tiết tại ",
    ):
        if marker in lowered:
            city = lowered.split(marker, 1)[1].strip(" ?!.,")
            for suffix in (
                "thế nào",
                "ra sao",
                "hôm nay",
                "bây giờ",
                "hiện tại",
                "như nào",
                "sao rồi",
            ):
                if city.endswith(suffix):
                    city = city[: -len(suffix)].strip(" ?!.,")
            return city.title() if city else "Hanoi"

    return "Hanoi"


def parse_rule_command(text: str) -> dict[str, object] | None:
    normalized = text.lower().strip()

    if any(phrase in normalized for phrase in ("tạm biệt", "tắt máy", "thoát")):
        return {"intent": "exit"}

    if any(phrase in normalized for phrase in ("dừng nhạc", "tắt nhạc", "ngừng nhạc")):
        return {"intent": "stop_music"}

    if any(
        phrase in normalized
        for phrase in ("phát nhạc", "mở nhạc", "bật nhạc", "phát bài", "mở bài", "bật bài")
    ):
        return {
            "intent": "play_music",
            "song_index": extract_song_index(normalized),
        }

    if "thời tiết" in normalized or "dự báo thời tiết" in normalized:
        return {
            "intent": "weather",
            "city": extract_city(normalized),
        }

    return None
