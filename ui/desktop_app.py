from __future__ import annotations

import math
import os
import queue
import struct
import threading
import tkinter as tk
from tkinter import messagebox

import pyaudio
import speech_recognition as sr

from config import get_settings
from core.assistant_service import AssistantReply, OllieAssistant
from core.env_store import load_env_settings, save_env_settings
from core.hearing import Ear

COLORS = {
    "bg": "#020812",
    "bg_alt": "#071421",
    "panel": "#081522",
    "panel_alt": "#0d1d2c",
    "border": "#17354e",
    "accent": "#1486bf",
    "accent_hover": "#1ea0dc",
    "accent_soft": "#54d8ff",
    "text": "#ffffff",
    "text_muted": "#9bb4cf",
    "text_soft": "#7fa1bf",
    "warning_bg": "#57341d",
    "warning_border": "#ffb866",
    "error_bg": "#5b1f2c",
    "error_border": "#ff6a89",
    "listening_bg": "#0c4967",
    "listening_border": "#54d8ff",
    "processing_bg": "#20355f",
    "processing_border": "#7fb0ff",
}

FONTS = {
    "title": ("Avenir Next", 34, "bold"),
    "subtitle": ("Avenir Next", 15),
    "status": ("Avenir Next", 12, "bold"),
    "hint": ("Avenir Next", 18, "bold"),
    "body": ("Avenir Next", 14),
    "body_small": ("Avenir Next", 12),
    "role": ("Avenir Next", 10, "bold"),
    "button": ("Avenir Next", 12, "bold"),
}


def _compute_level(frame: bytes) -> float:
    if not frame:
        return 0.0

    total = 0
    count = 0
    for (sample,) in struct.iter_unpack("<h", frame):
        total += sample * sample
        count += 1

    if count == 0:
        return 0.0

    rms = math.sqrt(total / count)
    return min(1.0, rms / 5000.0)


class AssistantWorker(threading.Thread):
    def __init__(
        self,
        assistant: OllieAssistant,
        text: str,
        speak_response: bool,
        event_queue: queue.Queue[tuple[str, object]],
    ):
        super().__init__(daemon=True)
        self.assistant = assistant
        self.text = text
        self.speak_response = speak_response
        self.event_queue = event_queue

    def run(self) -> None:
        try:
            reply = self.assistant.process_text(self.text, speak_response=self.speak_response)
            self.event_queue.put(("assistant_reply", reply))
        except Exception as e:
            self.event_queue.put(("assistant_error", str(e)))


class VoiceCaptureWorker(threading.Thread):
    def __init__(self, event_queue: queue.Queue[tuple[str, object]]):
        super().__init__(daemon=True)
        self.event_queue = event_queue
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        ear = Ear()
        if not ear.is_available:
            self.event_queue.put(
                ("voice_failed", ear.error_message or "Không tìm thấy microphone mặc định.")
            )
            return

        if ear.startup_message:
            self.event_queue.put(("voice_info", ear.startup_message))

        audio = pyaudio.PyAudio()
        stream = None
        sample_rate = 16000
        frames: list[bytes] = []

        try:
            try:
                device_info = audio.get_default_input_device_info()
                sample_rate = int(device_info.get("defaultSampleRate", 16000))
            except OSError:
                sample_rate = 16000
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                frames_per_buffer=1024,
            )

            while not self._stop_event.is_set():
                frame = stream.read(1024, exception_on_overflow=False)
                frames.append(frame)
                self.event_queue.put(("voice_level", _compute_level(frame)))
        except Exception as e:
            self.event_queue.put(("voice_failed", f"Không thể ghi âm từ microphone: {e}"))
            return
        finally:
            self.event_queue.put(("voice_level", 0.0))
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            audio.terminate()

        raw_audio = b"".join(frames)
        if not raw_audio:
            self.event_queue.put(("voice_failed", "Chưa ghi nhận được âm thanh nào."))
            return

        recognizer = sr.Recognizer()
        audio_data = sr.AudioData(raw_audio, sample_rate, 2)

        try:
            text = recognizer.recognize_google(audio_data, language="vi-VN")
        except sr.UnknownValueError:
            self.event_queue.put(("voice_failed", "OLLIE không nghe rõ bạn nói gì."))
            return
        except sr.RequestError:
            self.event_queue.put(
                ("voice_failed", "Không thể kết nối dịch vụ nhận dạng giọng nói lúc này.")
            )
            return
        except OSError as e:
            self.event_queue.put(
                ("voice_failed", f"Thiếu công cụ hệ thống để xử lý âm thanh: {e}")
            )
            return

        normalized = text.strip().lower()
        if not normalized:
            self.event_queue.put(("voice_failed", "OLLIE chưa nhận được nội dung hợp lệ."))
            return

        self.event_queue.put(("voice_transcript", normalized))


class SoundVisualizer(tk.Canvas):
    def __init__(self, master: tk.Misc):
        super().__init__(
            master,
            width=560,
            height=96,
            bg=COLORS["bg"],
            highlightthickness=0,
            bd=0,
        )
        self._active = False
        self._target_level = 0.0
        self._display_level = 0.0
        self._phase = 0.0
        self.after(30, self._tick)

    def set_active(self, value: bool) -> None:
        self._active = value
        if not value:
            self._target_level = 0.0

    def set_level(self, level: float) -> None:
        self._target_level = max(0.0, min(1.0, level))

    def _tick(self) -> None:
        floor = 0.08 if self._active else 0.0
        target = max(self._target_level, floor)
        self._display_level = (self._display_level * 0.72) + (target * 0.28)
        self._target_level *= 0.55
        if not self._active and self._display_level < 0.01:
            self._display_level = 0.0
        self._phase += 0.18
        self._draw()
        self.after(30, self._tick)

    def _draw(self) -> None:
        self.delete("all")
        width = int(self["width"])
        height = int(self["height"])
        margin = 28
        bar_count = 27
        center = (bar_count - 1) / 2.0
        usable_width = max(1, width - (margin * 2))
        spacing = usable_width / max(1, bar_count - 1)
        max_height = height - 16
        center_y = height / 2

        for index in range(bar_count):
            distance = abs(index - center) / center
            envelope = max(0.14, 1.0 - distance**1.6)
            ripple = 0.66 + (0.34 * math.sin(self._phase + (index * 0.42)))
            strength = min(1.0, self._display_level * envelope * ripple * 1.5)
            bar_height = max(10.0, strength * max_height)
            x = margin + (index * spacing)
            y1 = center_y - (bar_height / 2.0)
            y2 = center_y + (bar_height / 2.0)
            color = COLORS["accent_soft"] if strength >= 0.1 else "#17324a"
            if not self._active and strength < 0.1:
                color = "#0d2133"

            self.create_line(
                x,
                y1,
                x,
                y2,
                width=8,
                capstyle=tk.ROUND,
                fill=color,
            )


class MicButton(tk.Canvas):
    def __init__(self, master: tk.Misc, command):
        super().__init__(
            master,
            width=220,
            height=220,
            bg=COLORS["bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.command = command
        self._listening = False
        self._enabled = True
        self._pulse = 0.0
        self.bind("<Button-1>", self._on_click)
        self.after(32, self._tick)

    def set_listening(self, value: bool) -> None:
        self._listening = value
        self._draw()

    def set_enabled(self, value: bool) -> None:
        self._enabled = value
        self.configure(cursor="hand2" if value else "arrow")
        self._draw()

    def _on_click(self, _event) -> None:
        if self._enabled:
            self.command()

    def _tick(self) -> None:
        if self._listening:
            self._pulse = (self._pulse + 0.05) % 1.0
        elif self._pulse != 0.0:
            self._pulse = 0.0
        self._draw()
        self.after(32, self._tick)

    def _draw(self) -> None:
        self.delete("all")
        size = 220
        center = size / 2
        radius = 84

        if self._listening:
            pulse_radius = radius + 24 + (self._pulse * 18)
            self.create_oval(
                center - pulse_radius,
                center - pulse_radius,
                center + pulse_radius,
                center + pulse_radius,
                outline="#24587a",
                width=2,
            )

        outer_fill = "#071725" if self._enabled else "#08111a"
        inner_fill = "#14314a" if self._listening else "#0e2740"
        border = COLORS["accent_soft"] if self._listening else "#2d85b7"

        self.create_oval(
            center - radius,
            center - radius,
            center + radius,
            center + radius,
            fill=outer_fill,
            outline="",
        )
        self.create_oval(
            center - (radius - 12),
            center - (radius - 12),
            center + (radius - 12),
            center + (radius - 12),
            fill=inner_fill,
            outline=border,
            width=3,
        )

        icon_color = COLORS["text"] if self._enabled else COLORS["text_soft"]
        self.create_oval(
            center - 18,
            center - 52,
            center + 18,
            center + 4,
            outline=icon_color,
            width=6,
        )
        self.create_arc(
            center - 30,
            center - 6,
            center + 30,
            center + 42,
            start=205,
            extent=130,
            style=tk.ARC,
            outline=icon_color,
            width=6,
        )
        self.create_line(center, center + 8, center, center + 42, fill=icon_color, width=6)
        self.create_line(
            center - 18,
            center + 48,
            center + 18,
            center + 48,
            fill=icon_color,
            width=6,
        )


class SettingsDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, on_saved):
        super().__init__(master)
        self.on_saved = on_saved
        self.title("Settings")
        self.configure(bg=COLORS["bg_alt"])
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        values = load_env_settings()

        content = tk.Frame(self, bg=COLORS["bg_alt"], padx=24, pady=22)
        content.pack(fill="both", expand=True)

        self.entries: dict[str, tk.Entry] = {}
        fields = (
            ("GEMINI_API_KEY", "Gemini API Key"),
            ("WEATHER_API_KEY", "Weather API Key"),
            ("GEMINI_MODEL", "Gemini Model"),
            ("REQUEST_TIMEOUT", "Request Timeout"),
        )

        for row, (key, label_text) in enumerate(fields):
            label = tk.Label(
                content,
                text=label_text,
                bg=COLORS["bg_alt"],
                fg=COLORS["text"],
                font=FONTS["body_small"],
                anchor="w",
            )
            label.grid(row=row, column=0, sticky="w", pady=(0, 10))

            entry = tk.Entry(
                content,
                width=40,
                bg=COLORS["panel_alt"],
                fg=COLORS["text"],
                insertbackground=COLORS["text"],
                highlightthickness=1,
                highlightbackground=COLORS["border"],
                highlightcolor=COLORS["accent"],
                relief="flat",
                font=FONTS["body_small"],
            )
            entry.insert(0, values.get(key, ""))
            if key.endswith("API_KEY"):
                entry.configure(show="*")
            entry.grid(row=row, column=1, sticky="ew", padx=(18, 0), pady=(0, 10), ipady=7)
            self.entries[key] = entry

        content.grid_columnconfigure(1, weight=1)

        helper = tk.Label(
            content,
            text="Save xong thì đóng và mở lại OLLIE nếu bạn thay đổi API key.",
            bg=COLORS["bg_alt"],
            fg=COLORS["text_muted"],
            justify="left",
            wraplength=420,
            font=FONTS["body_small"],
        )
        helper.grid(row=len(fields), column=0, columnspan=2, sticky="w", pady=(4, 18))

        button_row = tk.Frame(content, bg=COLORS["bg_alt"])
        button_row.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="e")

        cancel_button = tk.Button(
            button_row,
            text="Cancel",
            command=self.destroy,
            bg="#102131",
            fg=COLORS["text"],
            activebackground="#163249",
            activeforeground=COLORS["text"],
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            font=FONTS["button"],
        )
        cancel_button.pack(side="left", padx=(0, 10))

        save_button = tk.Button(
            button_row,
            text="Save",
            command=self.save,
            bg=COLORS["accent"],
            fg=COLORS["text"],
            activebackground=COLORS["accent_hover"],
            activeforeground=COLORS["text"],
            relief="flat",
            bd=0,
            padx=16,
            pady=8,
            font=FONTS["button"],
        )
        save_button.pack(side="left")

        self.bind("<Escape>", lambda _event: self.destroy())
        self.after(20, self._center_on_parent)

    def _center_on_parent(self) -> None:
        parent = self.master
        self.update_idletasks()
        width = max(520, self.winfo_reqwidth())
        height = max(300, self.winfo_reqheight())
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + max(0, (parent_width - width) // 2)
        y = parent_y + max(0, (parent_height - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def save(self) -> None:
        save_env_settings({key: entry.get() for key, entry in self.entries.items()})
        self.on_saved()
        self.destroy()


class OllieDesktopApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OLLIE Desktop")
        self.root.geometry("1120x760")
        self.root.minsize(920, 680)
        self.root.configure(bg=COLORS["bg"])
        self.root.option_add("*tearOff", False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.settings = get_settings()
        self.assistant = OllieAssistant(self.settings)
        self.event_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.assistant_worker: AssistantWorker | None = None
        self.voice_worker: VoiceCaptureWorker | None = None
        self.history_revealed = False

        self._build_menu()
        self._build_ui()
        self._set_status("Nhấn vào microphone để bắt đầu trò chuyện.", "idle")
        self.root.after(40, self._poll_events)

        self_test_ms = os.getenv("OLLIE_GUI_SELF_TEST_MS", "").strip()
        if self_test_ms.isdigit():
            self.root.after(int(self_test_ms), self.root.destroy)

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self.root, bg=COLORS["panel"], fg=COLORS["text"])

        file_menu = tk.Menu(menu_bar, bg=COLORS["panel"], fg=COLORS["text"])
        file_menu.add_command(label="Exit", command=self.on_close)
        menu_bar.add_cascade(label="File", menu=file_menu)

        settings_menu = tk.Menu(menu_bar, bg=COLORS["panel"], fg=COLORS["text"])
        settings_menu.add_command(label="Open Settings", command=self.open_settings)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)

        tools_menu = tk.Menu(menu_bar, bg=COLORS["panel"], fg=COLORS["text"])
        tools_menu.add_command(label="Audio Diagnostics", command=self.show_diagnostics)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menu_bar, bg=COLORS["panel"], fg=COLORS["text"])
        help_menu.add_command(label="About OLLIE", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menu_bar)

    def _build_ui(self) -> None:
        self.container = tk.Frame(self.root, bg=COLORS["bg"], padx=40, pady=28)
        self.container.pack(fill="both", expand=True)

        header = tk.Frame(self.container, bg=COLORS["bg"])
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="OLLIE",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=FONTS["title"],
        )
        title.pack(pady=(0, 6))

        subtitle = tk.Label(
            header,
            text="Voice-first assistant",
            bg=COLORS["bg"],
            fg=COLORS["text_muted"],
            font=FONTS["subtitle"],
        )
        subtitle.pack()

        self.status_label = tk.Label(
            header,
            text="",
            bg=COLORS["panel_alt"],
            fg=COLORS["text"],
            font=FONTS["status"],
            padx=18,
            pady=10,
            wraplength=520,
            justify="center",
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        self.status_label.pack(pady=(16, 0))

        self.hero = tk.Frame(self.container, bg=COLORS["bg"])
        self.hero.pack(expand=True)

        self.visualizer = SoundVisualizer(self.hero)
        self.visualizer.pack(pady=(10, 20))

        self.mic_button = MicButton(self.hero, self.toggle_voice_capture)
        self.mic_button.pack()

        self.voice_hint = tk.Label(
            self.hero,
            text="Tap to speak",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=FONTS["hint"],
        )
        self.voice_hint.pack(pady=(18, 0))

        self.history_frame = tk.Frame(
            self.container,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            padx=22,
            pady=20,
        )

        history_title = tk.Label(
            self.history_frame,
            text="Conversation",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Avenir Next", 16, "bold"),
            anchor="w",
        )
        history_title.pack(fill="x", pady=(0, 12))

        history_body = tk.Frame(self.history_frame, bg=COLORS["panel"])
        history_body.pack(fill="both", expand=True)

        self.chat_view = tk.Text(
            history_body,
            bg=COLORS["bg_alt"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            relief="flat",
            wrap="word",
            padx=16,
            pady=14,
            font=FONTS["body"],
            height=12,
        )
        self.chat_view.pack(side="left", fill="both", expand=True)
        self.chat_view.configure(state="disabled")

        scrollbar = tk.Scrollbar(history_body, command=self.chat_view.yview)
        scrollbar.pack(side="right", fill="y")
        self.chat_view.configure(yscrollcommand=scrollbar.set)

        self.chat_view.tag_configure("role_user", foreground=COLORS["text_soft"], font=FONTS["role"])
        self.chat_view.tag_configure(
            "role_assistant", foreground=COLORS["text_soft"], font=FONTS["role"]
        )
        self.chat_view.tag_configure(
            "text_user", foreground="#9cdfff", spacing3=10, font=FONTS["body"]
        )
        self.chat_view.tag_configure(
            "text_assistant", foreground=COLORS["text"], spacing3=10, font=FONTS["body"]
        )
        self.chat_view.tag_configure(
            "text_system",
            foreground=COLORS["text_muted"],
            spacing3=10,
            font=("Avenir Next", 13, "italic"),
        )

        self.manual_row = tk.Frame(self.history_frame, bg=COLORS["panel"])

        self.manual_input = tk.Entry(
            self.manual_row,
            bg=COLORS["panel_alt"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"],
            relief="flat",
            font=FONTS["body_small"],
        )
        self.manual_input.pack(side="left", fill="x", expand=True, ipady=10)
        self.manual_input.bind("<Return>", lambda _event: self.submit_manual_text())

        self.manual_send_button = tk.Button(
            self.manual_row,
            text="Send",
            command=self.submit_manual_text,
            bg=COLORS["accent"],
            fg=COLORS["text"],
            activebackground=COLORS["accent_hover"],
            activeforeground=COLORS["text"],
            relief="flat",
            bd=0,
            padx=16,
            pady=10,
            font=FONTS["button"],
        )
        self.manual_send_button.pack(side="left", padx=(10, 0))

    def _poll_events(self) -> None:
        while True:
            try:
                event_name, payload = self.event_queue.get_nowait()
            except queue.Empty:
                break
            self._handle_event(event_name, payload)

        self.root.after(40, self._poll_events)

    def _handle_event(self, event_name: str, payload: object) -> None:
        if event_name == "voice_level":
            self.visualizer.set_level(float(payload))
            return

        if event_name == "voice_info":
            self._set_status(str(payload), "listening")
            return

        if event_name == "voice_failed":
            self.on_voice_failed(str(payload))
            return

        if event_name == "voice_transcript":
            self.on_voice_transcript(str(payload))
            return

        if event_name == "assistant_reply":
            self.on_assistant_reply(payload)
            return

        if event_name == "assistant_error":
            self.on_assistant_error(str(payload))

    def _set_status(self, text: str, mode: str) -> None:
        palette = {
            "idle": (COLORS["panel_alt"], COLORS["border"]),
            "listening": (COLORS["listening_bg"], COLORS["listening_border"]),
            "processing": (COLORS["processing_bg"], COLORS["processing_border"]),
            "warning": (COLORS["warning_bg"], COLORS["warning_border"]),
            "error": (COLORS["error_bg"], COLORS["error_border"]),
        }
        background, border = palette.get(mode, palette["idle"])
        self.status_label.configure(text=text, bg=background, highlightbackground=border)

    def reveal_history(self) -> None:
        if self.history_revealed:
            return

        self.history_revealed = True
        self.history_frame.pack(fill="both", expand=True, pady=(24, 0))

    def show_manual_input(self) -> None:
        if not self.manual_row.winfo_manager():
            self.manual_row.pack(fill="x", pady=(14, 0))
        self.manual_input.focus_set()

    def append_message(self, role: str, text: str) -> None:
        self.reveal_history()
        self.chat_view.configure(state="normal")

        if role == "user":
            self.chat_view.insert("end", "YOU\n", ("role_user",))
            self.chat_view.insert("end", f"{text}\n\n", ("text_user",))
        else:
            self.chat_view.insert("end", "OLLIE\n", ("role_assistant",))
            self.chat_view.insert("end", f"{text}\n\n", ("text_assistant",))

        self.chat_view.configure(state="disabled")
        self.chat_view.see("end")

    def append_system_message(self, text: str) -> None:
        self.reveal_history()
        self.chat_view.configure(state="normal")
        self.chat_view.insert("end", f"{text}\n\n", ("text_system",))
        self.chat_view.configure(state="disabled")
        self.chat_view.see("end")

    def toggle_voice_capture(self) -> None:
        if self.assistant_worker and self.assistant_worker.is_alive():
            self._set_status("OLLIE đang xử lý câu trả lời. Hãy đợi một chút.", "processing")
            return

        if self.voice_worker and self.voice_worker.is_alive():
            self.stop_listening()
            return

        self.start_listening()

    def start_listening(self) -> None:
        self.voice_worker = VoiceCaptureWorker(self.event_queue)
        self.visualizer.set_active(True)
        self.mic_button.set_listening(True)
        self.mic_button.set_enabled(True)
        self.voice_hint.configure(text="Listening... tap again to stop")
        self._set_status("OLLIE đang nghe bạn nói.", "listening")
        self.voice_worker.start()

    def stop_listening(self) -> None:
        if not self.voice_worker:
            return

        self.voice_hint.configure(text="Đang xử lý giọng nói...")
        self._set_status("Đang xử lý giọng nói vừa thu được.", "processing")
        self.voice_worker.stop()
        self.mic_button.set_enabled(False)

    def on_voice_failed(self, message: str) -> None:
        self.visualizer.set_active(False)
        self.visualizer.set_level(0.0)
        self.mic_button.set_listening(False)
        self.mic_button.set_enabled(True)
        self.voice_hint.configure(text="Tap to speak")
        self._set_status(message, "warning")
        self.append_system_message(message)
        self.show_manual_input()
        self.voice_worker = None

    def on_voice_transcript(self, transcript: str) -> None:
        self.visualizer.set_active(False)
        self.mic_button.set_listening(False)
        self.mic_button.set_enabled(True)
        self.voice_hint.configure(text="Tap to speak")
        self.append_message("user", transcript)
        self._set_status("OLLIE đang soạn câu trả lời...", "processing")
        self.voice_worker = None
        self.run_assistant(transcript, speak_response=True)

    def submit_manual_text(self) -> None:
        text = self.manual_input.get().strip()
        if not text:
            return

        self.manual_input.delete(0, "end")
        self.append_message("user", text)
        self._set_status("OLLIE đang xử lý yêu cầu văn bản...", "processing")
        self.run_assistant(text, speak_response=False)

    def run_assistant(self, text: str, speak_response: bool) -> None:
        if self.assistant_worker and self.assistant_worker.is_alive():
            self.append_system_message("OLLIE vẫn đang xử lý yêu cầu trước đó.")
            return

        self.assistant_worker = AssistantWorker(
            self.assistant,
            text,
            speak_response,
            self.event_queue,
        )
        self.assistant_worker.start()

    def on_assistant_reply(self, reply: object) -> None:
        if not isinstance(reply, AssistantReply):
            self.on_assistant_error("Không nhận được phản hồi hợp lệ từ hệ thống.")
            return

        self.append_message("assistant", reply.reply_text)
        if reply.status_text and reply.status_text != reply.reply_text:
            self.append_system_message(reply.status_text)

        if reply.should_exit:
            self._set_status("Session đã kết thúc. Bạn có thể nhấn mic để bắt đầu lại.", "idle")
        else:
            self._set_status("Nhấn vào microphone để tiếp tục trò chuyện.", "idle")

        self.assistant_worker = None

    def on_assistant_error(self, message: str) -> None:
        self.append_system_message(f"OLLIE gặp lỗi khi xử lý: {message}")
        self._set_status("OLLIE gặp lỗi trong lúc xử lý. Hãy thử lại.", "error")
        self.assistant_worker = None

    def open_settings(self) -> None:
        SettingsDialog(self.root, self._on_settings_saved)

    def _on_settings_saved(self) -> None:
        self.settings = get_settings()
        self.assistant = OllieAssistant(self.settings)
        self.append_system_message("Đã lưu Settings và nạp lại cấu hình.")
        self._set_status("Cấu hình mới đã được áp dụng.", "idle")

    def show_diagnostics(self) -> None:
        report = self.assistant.get_diagnostics_report()
        self.reveal_history()

        dialog = tk.Toplevel(self.root)
        dialog.title("Audio Diagnostics")
        dialog.configure(bg=COLORS["bg_alt"])
        dialog.geometry("760x580")
        dialog.transient(self.root)

        viewer = tk.Text(
            dialog,
            bg=COLORS["bg_alt"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            relief="flat",
            wrap="word",
            padx=14,
            pady=14,
            font=("SF Mono", 11),
        )
        viewer.pack(fill="both", expand=True, padx=18, pady=18)
        viewer.insert("1.0", report)
        viewer.configure(state="disabled")

    def show_about(self) -> None:
        messagebox.showinfo(
            "About OLLIE",
            "OLLIE Desktop đã được thiết kế lại theo hướng voice-first.\n"
            "Màn hình chính chỉ giữ microphone trung tâm, visualizer âm thanh và lịch sử hội thoại.",
        )

    def on_close(self) -> None:
        if self.voice_worker and self.voice_worker.is_alive():
            self.voice_worker.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def launch_desktop_app() -> int:
    app = OllieDesktopApp()
    app.run()
    return 0
