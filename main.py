import argparse
import pygame

from config import get_settings
from core.assistant_service import OllieAssistant
from core.hearing import Ear


def initialize_audio() -> bool:
    try:
        pygame.mixer.init()
        return True
    except pygame.error as e:
        print(f"System: Không thể khởi tạo âm thanh phát nhạc: {e}")
        print("System: OLLIE sẽ tiếp tục chạy, nhưng tính năng phát nhạc sẽ tạm thời không khả dụng.")
        return False


def read_text_command() -> str | None:
    try:
        text = input("Bạn nhập: ").strip()
    except EOFError:
        print("\nSystem: Không nhận được dữ liệu từ bàn phím. OLLIE sẽ thoát.")
        return "tạm biệt"
    except KeyboardInterrupt:
        print("\nSystem: Đã nhận yêu cầu dừng từ bàn phím.")
        return "tạm biệt"

    return text.lower() if text else None


def run_cli() -> int:
    settings = get_settings()

    print("--- KHỞI ĐỘNG OLLIE ---")

    if not settings.gemini_api_key:
        print("Lỗi: Chưa cấu hình GEMINI_API_KEY trong file .env")
        return 1

    audio_ready = initialize_audio()

    ear = Ear()
    assistant = OllieAssistant(settings)

    if ear.startup_message:
        print(f"System: {ear.startup_message}")

    if not ear.is_available:
        print(f"System: {ear.error_message}")
        print("System: OLLIE sẽ chuyển sang chế độ nhập lệnh bằng bàn phím.")

    if not audio_ready:
        print("System: Bạn vẫn có thể hỏi thời tiết, trò chuyện và dùng chế độ nhập text.")

    assistant.mouth.speak("Xin chào, tôi là Ollie. Tôi đã sẵn sàng.")

    while True:
        if ear.is_available:
            user_input = ear.listen()
        else:
            user_input = read_text_command()

        if not user_input:
            continue

        reply = assistant.process_text(user_input, speak_response=True)
        if reply.status_text:
            print(f"System: {reply.status_text}")
        if reply.should_exit:
            break

    return 0


def launch_desktop() -> int:
    try:
        from ui.desktop_app import launch_desktop_app
    except ImportError as e:
        print(f"Lỗi: không thể nạp giao diện desktop: {e}")
        print("Hãy kiểm tra dependency rồi chạy lại, hoặc dùng chế độ CLI bằng `python3 main.py --cli`.")
        return 1

    try:
        return launch_desktop_app()
    except Exception as e:
        print(f"Lỗi: không thể khởi động giao diện desktop: {e}")
        print("Bạn vẫn có thể dùng chế độ CLI bằng `python3 main.py --cli`.")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OLLIE desktop assistant")
    parser.add_argument("--cli", action="store_true", help="Run the legacy CLI mode")
    args = parser.parse_args()
    raise SystemExit(run_cli() if args.cli else launch_desktop())
