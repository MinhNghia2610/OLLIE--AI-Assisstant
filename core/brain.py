from google import genai
from google.genai import types


class Brain:
    def __init__(self, api_key: str, model_name: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def think(self, user_text: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_text,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Bạn là trợ lý giọng nói tên Ollie. "
                        "Trả lời ngắn gọn, tự nhiên, lịch sự bằng tiếng Việt."
                    ),
                    temperature=0.4,
                    max_output_tokens=250,
                ),
            )
            text = (response.text or "").strip()
            return text or "Mình chưa có câu trả lời phù hợp."
        except Exception as e:
            print(f"Brain error: {e}")
            return "Não bộ đang bị nhiễu sóng."
