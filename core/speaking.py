import shutil
import subprocess
import unicodedata

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


class Mouth:
    def __init__(self):
        self.say_path = shutil.which("say")
        self.engine = None

        if not self.say_path and pyttsx3 is not None:
            try:
                self.engine = pyttsx3.init()

                # optimize voice speed + quality
                self.engine.setProperty("rate", 175)

            except Exception:
                self.engine = None

    def _clean_text(self, text: str) -> str:
        """
        Normalize text để tránh lỗi TTS (emoji / unicode / dấu tiếng Việt)
        """
        text = unicodedata.normalize("NFKC", text)
        return text.strip()

    def speak(self, text: str) -> None:
        if not text:
            return

        text = self._clean_text(text)

        print(f"OLLIE: {text}")

        try:
            # macOS native TTS (best quality)
            if self.say_path:
                subprocess.run(
                    [self.say_path, text],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return

            # fallback pyttsx3
            if self.engine is not None:
                self.engine.say(text)
                self.engine.runAndWait()
                return

            print("❌ Không có TTS backend khả dụng.")

        except Exception as e:
            print(f"❌ Lỗi TTS: {e}")