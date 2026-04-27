import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import tempfile
import os


class Ear:
    def __init__(self):
        self.sample_rate = 16000

    def listen(self, duration=5):
        """
        Thu âm từ microphone và trả về file WAV path
        (PRO stable version)
        """

        try:
            print("🎤 OLLIE đang nghe...")

            # record audio
            audio = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16"
            )
            sd.wait()

            # create safe temp file
            fd, path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)  # important fix for macOS stability

            # write wav file
            write(path, self.sample_rate, audio)

            print("✅ Đã thu âm xong")
            return path

        except Exception as e:
            print(f"❌ Lỗi micro: {e}")
            return None