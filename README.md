<div align="center">

# 🤖 OLLIE — AI Voice Assistant

**A Vietnamese-first AI Voice Assistant powered by Google Gemini**

## Overview

OLLIE is a desktop AI voice assistant built in Python, designed with Vietnamese as its primary language. It listens to your voice commands, understands natural language via Google Gemini, controls music playback, fetches live weather data, and responds with text-to-speech output. OLLIE supports both a graphical desktop UI and a lightweight CLI mode.

---

## ✨ Features

- 🎙️ **Voice Recognition** — Captures voice input via microphone using Google Speech Recognition (vi-VN)
- 🧠 **AI Chat** — Powered by Google Gemini 2.5 Flash for natural, context-aware Vietnamese responses
- 🎵 **Music Playback** — Play, stop, and select specific tracks from a local music library
- 🌤️ **Live Weather** — Real-time weather data via OpenWeatherMap API for any city
- 🔊 **Text-to-Speech** — Speaks responses aloud using macOS `say` or `pyttsx3` fallback
- 💻 **Dual Mode** — Runs as a desktop GUI app or a terminal CLI
- ⌨️ **Keyboard Fallback** — Automatically switches to text input if no microphone is detected

---

## 🏗️ Architecture

```
OLLIE/
├── main.py                  # Entry point (CLI + Desktop launcher)
├── config.py                # Settings loader from .env
├── core/
│   ├── assistant_service.py # Central orchestrator
│   ├── brain.py             # Gemini AI integration
│   ├── commands.py          # Rule-based Vietnamese NLP parser
│   ├── skills.py            # Music & Weather executors
│   ├── hearing.py           # Microphone → Speech-to-Text
│   ├── speaking.py          # Text-to-Speech output
│   └── diagnostics.py       # Runtime system diagnostics
├── ui/
│   └── desktop_app.py       # Tkinter desktop GUI
├── assets/
│   └── music/               # Local MP3 library
├── tests/                   # Full unit test suite (24 tests)
└── requirements.txt
```

### Processing Flow

```
User Voice / Keyboard
        ↓
    core/hearing.py  (STT)
        ↓
 core/commands.py  (rule-based NLP)
    ↙         ↘
Known command    Unknown → core/brain.py (Gemini AI)
    ↓                         ↓
core/skills.py          AI response text
(music / weather)             ↓
        ↘               ↙
         core/speaking.py (TTS)
```

---

## 📋 Requirements

- Python 3.10 or higher
- A working microphone (optional — keyboard fallback available)
- API keys for Gemini and OpenWeatherMap

### Python Dependencies

```
SpeechRecognition==3.10.1
pygame==2.5.2
google-genai==1.66.0
requests==2.31.0
python-dotenv==1.0.1
pyaudio           # optional — for audio device diagnostics
pyttsx3>=2.90     # optional — TTS fallback (non-macOS)
setuptools>=82
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/MinhNghia2610/OLLIE--AI-Assisstant.git
cd OLLIE--AI-Assisstant
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `pyaudio` requires the PortAudio system library. If installation fails, skip it — OLLIE runs without it. On macOS: `brew install portaudio` then retry.

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
WEATHER_API_KEY=your_openweathermap_key_here
GEMINI_MODEL=gemini-2.5-flash
REQUEST_TIMEOUT=10
```

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | Google AI Studio API key |
| `WEATHER_API_KEY` | ⚠️ Optional | OpenWeatherMap API key |
| `GEMINI_MODEL` | ⚠️ Optional | Defaults to `gemini-2.5-flash` |
| `REQUEST_TIMEOUT` | ⚠️ Optional | Defaults to `10` seconds |

---

## 🚀 Running OLLIE

### Desktop mode (default)

```bash
python3 main.py
```

### CLI mode

```bash
python3 main.py --cli
```

---

## 🗣️ Supported Voice Commands

| Command (Vietnamese) | Example | Action |
|---|---|---|
| Play music | `"bật nhạc"` / `"phát bài 3"` | Play track (random or by index) |
| Stop music | `"dừng nhạc"` / `"tắt nhạc"` | Stop current playback |
| Weather | `"thời tiết ở Hà Nội"` | Fetch live weather for city |
| Exit | `"tạm biệt"` / `"tắt máy"` | Gracefully shut down OLLIE |
| Anything else | Any natural speech | Forwarded to Gemini AI |

---

## 🧪 Running Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run a specific module
python3 -m pytest tests/test_commands.py -v
python3 -m pytest tests/test_skills.py -v
python3 -m pytest tests/test_hearing.py -v
python3 -m pytest tests/test_assistant_service.py -v
python3 -m pytest tests/test_main.py -v
```

**Current test status: ✅ 24/24 PASSED**

---

## 🐛 Known Issues & Notes

- **Python 3.13 compatibility:** `SpeechRecognition 3.10.1` uses deprecated `aifc` and `audioop` modules that will be removed in Python 3.13. Upgrade to `SpeechRecognition>=3.11` before migrating.
- **pyaudio is optional:** The `diagnostics.py` module degrades gracefully when `pyaudio` is not installed.
- **TTS on non-macOS:** The `say` command is macOS-only. On Windows/Linux, OLLIE uses `pyttsx3` as a fallback. Voice quality may differ.
- **Music directory:** Place `.mp3` files in `assets/music/`. OLLIE refers to tracks by index (Bài 1, Bài 2…).

---

## 📁 Project Structure Detail

```
tests/
├── test_commands.py          # NLP parser logic (8 tests)
├── test_skills.py            # Music & Weather skills (5 tests)
├── test_hearing.py           # Microphone / STT module (2 tests)
├── test_assistant_service.py # Core orchestrator (4 tests)
└── test_main.py              # Entry point & CLI flow (5 tests)
```

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

---

# 🇻🇳 Phiên Bản Tiếng Việt

## Tổng quan

OLLIE là một trợ lý AI giọng nói chạy trên desktop, được viết bằng Python, lấy tiếng Việt làm ngôn ngữ chính. OLLIE lắng nghe lệnh thoại, hiểu ngôn ngữ tự nhiên thông qua Google Gemini, điều khiển phát nhạc, lấy thông tin thời tiết thực tế và phản hồi bằng giọng đọc. OLLIE hỗ trợ cả giao diện desktop lẫn chế độ dòng lệnh (CLI).

---

## ✨ Tính năng

- 🎙️ **Nhận diện giọng nói** — Thu âm từ microphone và chuyển đổi bằng Google Speech Recognition (vi-VN)
- 🧠 **Chat AI** — Sử dụng Google Gemini 2.5 Flash để trả lời tự nhiên bằng tiếng Việt
- 🎵 **Phát nhạc** — Phát, dừng và chọn bài hát cụ thể từ thư viện nhạc cục bộ
- 🌤️ **Thời tiết thực tế** — Dữ liệu thời tiết trực tiếp qua OpenWeatherMap API cho bất kỳ thành phố nào
- 🔊 **Đọc văn bản (TTS)** — Phản hồi bằng giọng đọc, ưu tiên `say` (macOS), dự phòng `pyttsx3`
- 💻 **Hai chế độ** — Chạy dưới dạng ứng dụng desktop có giao diện hoặc CLI trên terminal
- ⌨️ **Dự phòng bàn phím** — Tự động chuyển sang nhập văn bản nếu không tìm thấy microphone

---

## 🏗️ Kiến trúc hệ thống

```
OLLIE/
├── main.py                  # Điểm khởi động (CLI + Desktop)
├── config.py                # Tải cấu hình từ .env
├── core/
│   ├── assistant_service.py # Bộ điều phối trung tâm
│   ├── brain.py             # Tích hợp Gemini AI
│   ├── commands.py          # Phân tích lệnh tiếng Việt theo quy tắc
│   ├── skills.py            # Xử lý nhạc & thời tiết
│   ├── hearing.py           # Microphone → Speech-to-Text
│   ├── speaking.py          # Text-to-Speech đầu ra
│   └── diagnostics.py       # Kiểm tra hệ thống runtime
├── ui/
│   └── desktop_app.py       # Giao diện Tkinter
├── assets/
│   └── music/               # Thư viện nhạc MP3 cục bộ
├── tests/                   # Bộ test đầy đủ (24 test cases)
└── requirements.txt
```

### Luồng xử lý

```
Giọng nói / Bàn phím của người dùng
        ↓
    core/hearing.py  (Nhận diện giọng nói)
        ↓
 core/commands.py  (Phân tích lệnh theo quy tắc)
    ↙                      ↘
Lệnh quen thuộc        Không rõ → core/brain.py (Gemini AI)
    ↓                              ↓
core/skills.py                 Văn bản phản hồi AI
(nhạc / thời tiết)                 ↓
        ↘                     ↙
         core/speaking.py (Đọc phản hồi)
```

---

## 📋 Yêu cầu hệ thống

- Python 3.10 trở lên
- Microphone (tuỳ chọn — có thể dùng bàn phím thay thế)
- API key của Gemini và OpenWeatherMap

### Thư viện Python cần thiết

```
SpeechRecognition==3.10.1
pygame==2.5.2
google-genai==1.66.0
requests==2.31.0
python-dotenv==1.0.1
pyaudio           # tuỳ chọn — kiểm tra thiết bị âm thanh
pyttsx3>=2.90     # tuỳ chọn — TTS dự phòng (không phải macOS)
setuptools>=82
```

---

## ⚙️ Cài đặt

### 1. Clone repository

```bash
git clone https://github.com/MinhNghia2610/OLLIE--AI-Assisstant.git
cd OLLIE--AI-Assisstant
```

### 2. Tạo môi trường ảo

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

> **Lưu ý:** `pyaudio` yêu cầu thư viện hệ thống PortAudio. Nếu cài không được, có thể bỏ qua — OLLIE vẫn chạy bình thường. Trên macOS: `brew install portaudio` rồi cài lại.

### 4. Cấu hình biến môi trường

Tạo file `.env` tại thư mục gốc của dự án:

```env
GEMINI_API_KEY=your_gemini_api_key_here
WEATHER_API_KEY=your_openweathermap_key_here
GEMINI_MODEL=gemini-2.5-flash
REQUEST_TIMEOUT=10
```

| Biến | Bắt buộc | Mô tả |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Có | API key từ Google AI Studio |
| `WEATHER_API_KEY` | ⚠️ Không bắt buộc | API key từ OpenWeatherMap |
| `GEMINI_MODEL` | ⚠️ Không bắt buộc | Mặc định là `gemini-2.5-flash` |
| `REQUEST_TIMEOUT` | ⚠️ Không bắt buộc | Mặc định `10` giây |

---

## 🚀 Chạy OLLIE

### Chế độ Desktop (mặc định)

```bash
python3 main.py
```

### Chế độ CLI

```bash
python3 main.py --cli
```

---

## 🗣️ Các lệnh thoại được hỗ trợ

| Lệnh | Ví dụ | Hành động |
|---|---|---|
| Phát nhạc | `"bật nhạc"` / `"phát bài 3"` | Phát bài hát (ngẫu nhiên hoặc theo số) |
| Dừng nhạc | `"dừng nhạc"` / `"tắt nhạc"` | Dừng phát nhạc hiện tại |
| Thời tiết | `"thời tiết ở Hà Nội"` | Lấy thông tin thời tiết theo thành phố |
| Thoát | `"tạm biệt"` / `"tắt máy"` | Tắt OLLIE |
| Bất cứ điều gì khác | Câu hỏi tự nhiên bất kỳ | Chuyển sang Gemini AI xử lý |

---

## 🧪 Chạy kiểm thử

```bash
# Chạy toàn bộ test suite
python3 -m pytest tests/ -v

# Chạy từng module riêng
python3 -m pytest tests/test_commands.py -v
python3 -m pytest tests/test_skills.py -v
python3 -m pytest tests/test_hearing.py -v
python3 -m pytest tests/test_assistant_service.py -v
python3 -m pytest tests/test_main.py -v
```

**Kết quả hiện tại: ✅ 24/24 PASSED**

---

## 🐛 Vấn đề đã biết & Ghi chú

- **Tương thích Python 3.13:** `SpeechRecognition 3.10.1` dùng các module `aifc` và `audioop` sẽ bị xoá trong Python 3.13. Cần nâng lên `SpeechRecognition>=3.11` trước khi chuyển sang Python 3.13.
- **pyaudio là tuỳ chọn:** Module `diagnostics.py` hoạt động bình thường kể cả khi không có `pyaudio`.
- **TTS trên Windows/Linux:** Lệnh `say` chỉ có trên macOS. Trên hệ thống khác, OLLIE dùng `pyttsx3` thay thế, chất lượng giọng có thể khác.
- **Thư mục nhạc:** Đặt file `.mp3` vào `assets/music/`. OLLIE nhận diện bài theo thứ tự số (Bài 1, Bài 2…).

---

## 📁 Chi tiết cấu trúc Test

```
tests/
├── test_commands.py          # Parser NLP tiếng Việt (8 tests)
├── test_skills.py            # Kỹ năng nhạc & thời tiết (5 tests)
├── test_hearing.py           # Module microphone / STT (2 tests)
├── test_assistant_service.py # Bộ điều phối trung tâm (4 tests)
└── test_main.py              # Entry point & luồng CLI (5 tests)
```

---

## 📄 Giấy phép

MIT License — tự do sử dụng, chỉnh sửa và phân phối.
