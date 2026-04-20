import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not api_key:
    raise RuntimeError("Chưa cấu hình GEMINI_API_KEY trong file .env")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model=model_name,
        contents="Chào bạn",
    )
    print("Kết nối thành công! Gemini trả lời:", response.text)
except Exception as e:
    print("Thất bại! Lỗi là:", e)
