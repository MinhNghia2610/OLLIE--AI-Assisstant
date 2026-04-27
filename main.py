import argparse
import pygame

from config import get_settings
from core.assistant_service import OllieAssistant
from core.hearing import Ear


# =========================
# AUDIO INIT
# =========================
def initialize_audio() -> bool:
    try:
        pygame.mixer.init()
        return True
    except pygame.error as e:
        print(f"System: Không thể khởi tạo audio: {e}")
        print("System: Nhạc sẽ bị vô hiệu hóa.")
        return False


# =========================
# TEXT INPUT FALLBACK
# =========================
def read_text_command() -> str | None:
    try:
        text = input("Bạn nhập: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nSystem: Thoát CLI.")
        return "tạm biệt"

    return text.lower() if text else None


# =========================
# CLI MODE
# =========================
def run_cli() -> int:
    settings = get_settings()

    print("🚀 KHỞI ĐỘNG OLLIE...")

    if not settings.gemini_api_key:
        print("❌ Thiếu GEMINI_API_KEY")
        return 1

    audio_ready = initialize_audio()

    ear = Ear()
    assistant = OllieAssistant(settings)

    # status
    if ear.startup_message:
        print(f"System: {ear.startup_message}")

    if not ear.is_available:
        print(f"⚠️ Mic lỗi: {ear.error_message}")
        print("System: chuyển sang bàn phím.")

    if not audio_ready:
        print("System: Audio disabled (music off)")

    assistant.mouth.speak("Xin chào, tôi là Ollie.")

    try:
        while True:
            # INPUT
            if ear.is_available:
                user_input = ear.listen()
            else:
                user_input = read_text_command()

            if not user_input:
                continue

            # PROCESS
            reply = assistant.process_text(user_input, speak_response=True)

            if reply.status_text:
                print(f"System: {reply.status_text}")

            if reply.should_exit:
                break

    except KeyboardInterrupt:
        print("\nSystem: Dừng chương trình.")

    finally:
        # cleanup
        pygame.mixer.quit()

    return 0


# =========================
# DESKTOP MODE
# =========================
def launch_desktop() -> int:
    try:
        from ui.desktop_app import launch_desktop_app
        return launch_desktop_app()
    except Exception as e:
        print(f"❌ Lỗi UI: {e}")
        print("Chuyển sang CLI: python3 main.py --cli")
        return 1


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OLLIE Assistant")
    parser.add_argument("--cli", action="store_true", help="Run CLI mode")
    args = parser.parse_args()

    raise SystemExit(run_cli() if args.cli else launch_desktop())