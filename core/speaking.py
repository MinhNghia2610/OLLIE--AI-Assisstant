import shutil
import subprocess

try:
    import pyttsx3
except ImportError:  # pragma: no cover - optional dependency at runtime
    pyttsx3 = None


class Mouth:
    def __init__(self):
        self.say_path = shutil.which("say")
        self.engine = None

        if not self.say_path and pyttsx3 is not None:
            try:
                self.engine = pyttsx3.init()
            except Exception:
                self.engine = None

    def speak(self, text: str) -> None:
        if not text:
            return

        print(f"OLLIE: {text}")

        try:
            if self.say_path:
                subprocess.run([self.say_path, text], check=True)
                return

            if self.engine is not None:
                self.engine.say(text)
                self.engine.runAndWait()
                return

            print("Lỗi module nói: không tìm thấy backend TTS phù hợp trên hệ thống.")
        except Exception as e:
            print(f"Lỗi module nói: {e}")
