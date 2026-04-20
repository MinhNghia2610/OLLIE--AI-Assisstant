import speech_recognition as sr


class Ear:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.error_message = None
        self.error_details = None
        self.startup_message = None
        self.selected_device_index = None
        self.selected_device_name = "Default Microphone"

        self._initialize_microphone()

    @property
    def is_available(self) -> bool:
        return self.microphone is not None

    def _initialize_microphone(self) -> None:
        try:
            self.microphone = sr.Microphone()
            self.startup_message = "Đang dùng microphone mặc định của laptop."
            self.error_message = None
            self.error_details = None
        except OSError as e:
            self.error_details = str(e)
            self.error_message = self._build_error_message(e)
        except Exception as e:
            self.error_details = str(e)
            self.error_message = self._build_error_message(e)

    def _build_error_message(self, error: Exception) -> str:
        details = str(error).strip()

        if "No Default Input Device Available" in details:
            return (
                "Không tìm thấy microphone mặc định. "
                "Hãy chọn MacBook Microphone trong System Settings > Sound > Input "
                "và cấp quyền Microphone cho ứng dụng đang chạy OLLIE."
            )

        if "distutils" in details:
            return (
                "Thiếu dependency Python để khởi tạo microphone. "
                "Hãy cài lại môi trường OLLIE với setuptools."
            )

        return "Không thể khởi tạo microphone mặc định."

    def listen(self):
        """Thu âm và chuyển đổi thành văn bản tiếng Việt."""
        if not self.microphone:
            return None

        print("OLLIE đang nghe...", end="\r")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio, language="vi-VN")
                print(f"\nBạn nói: {text}")
                return text.lower()
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                print("\nOLLIE không nghe rõ bạn nói gì.")
                return None
            except sr.RequestError:
                print("\nLỗi kết nối dịch vụ nhận dạng giọng nói.")
                return None
            except OSError as e:
                print(f"\nThiếu công cụ hệ thống để xử lý âm thanh: {e}")
                return None
