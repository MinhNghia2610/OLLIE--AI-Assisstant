from dataclasses import dataclass

import pygame

from config import Settings
from core.brain import Brain
from core.commands import parse_rule_command
from core.diagnostics import collect_runtime_diagnostics, format_runtime_diagnostics
from core.skills import Skills
from core.speaking import Mouth


@dataclass
class AssistantReply:
    user_text: str
    reply_text: str
    intent: str
    status_text: str | None = None
    should_exit: bool = False


class OllieAssistant:
    def __init__(
        self,
        settings: Settings,
        *,
        brain: Brain | None = None,
        skills: Skills | None = None,
        mouth: Mouth | None = None,
    ):
        self.settings = settings
        self.mouth = mouth or Mouth()

        self.skills = skills or Skills(
            music_dir=settings.music_dir,
            weather_api_key=settings.weather_api_key,
            request_timeout=settings.request_timeout,
        )

        self.brain = brain
        if self.brain is None and settings.gemini_api_key:
            self.brain = Brain(
                api_key=settings.gemini_api_key,
                model_name=settings.model_name,
            )

    # =========================
    # AUDIO SYSTEM SAFETY
    # =========================
    def ensure_music_ready(self) -> tuple[bool, str | None]:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            return True, None
        except Exception as e:
            return False, f"Lỗi khởi tạo audio system: {e}"

    # =========================
    # MAIN PROCESSOR
    # =========================
    def process_text(self, user_text: str, *, speak_response: bool = False) -> AssistantReply:
        clean_text = user_text.strip()

        if not clean_text:
            reply = AssistantReply(
                user_text=user_text,
                reply_text="Mình chưa nghe rõ nội dung.",
                intent="empty",
            )
            self._maybe_speak(reply, speak_response)
            return reply

        # =========================
        # RULE-BASED COMMANDS FIRST
        # =========================
        command = parse_rule_command(clean_text)

        if command:
            intent = str(command.get("intent"))

            # EXIT
            if intent == "exit":
                self.skills.stop_music()
                reply = AssistantReply(
                    user_text=clean_text,
                    reply_text="Tạm biệt bạn 👋",
                    intent=intent,
                    should_exit=True,
                )
                self._maybe_speak(reply, speak_response)
                return reply

            # STOP MUSIC
            if intent == "stop_music":
                status = self.skills.stop_music()
                reply = AssistantReply(
                    user_text=clean_text,
                    reply_text=status,
                    intent=intent,
                    status_text=status,
                )
                self._maybe_speak(reply, speak_response)
                return reply

            # PLAY MUSIC
            if intent == "play_music":
                ready, error = self.ensure_music_ready()
                if not ready:
                    reply = AssistantReply(
                        user_text=clean_text,
                        reply_text=error or "Không thể khởi tạo audio.",
                        intent=intent,
                        status_text=error,
                    )
                    self._maybe_speak(reply, speak_response)
                    return reply

                status = self.skills.play_music(command.get("song_index"))
                reply = AssistantReply(
                    user_text=clean_text,
                    reply_text=status,
                    intent=intent,
                    status_text=status,
                )
                self._maybe_speak(reply, speak_response)
                return reply

            # WEATHER
            if intent == "weather":
                city = str(command.get("city", ""))
                weather_info = self.skills.get_weather(city)

                reply = AssistantReply(
                    user_text=clean_text,
                    reply_text=weather_info,
                    intent=intent,
                )
                self._maybe_speak(reply, speak_response)
                return reply

        # =========================
        # AI FALLBACK
        # =========================
        if not self.brain:
            reply = AssistantReply(
                user_text=clean_text,
                reply_text="Chưa cấu hình AI (thiếu Gemini API key).",
                intent="chat_unavailable",
            )
            self._maybe_speak(reply, speak_response)
            return reply

        try:
            ai_response = self.brain.think(clean_text)
        except Exception as e:
            ai_response = f"AI gặp lỗi: {e}"

        reply = AssistantReply(
            user_text=clean_text,
            reply_text=ai_response,
            intent="chat",
        )

        self._maybe_speak(reply, speak_response)
        return reply

    # =========================
    # STATUS
    # =========================
    def get_status_overview(self) -> dict[str, str]:
        music_files = self.skills._scan_music()

        return {
            "Gemini": "Ready" if self.settings.gemini_api_key else "Missing key",
            "Weather": "Ready" if self.settings.weather_api_key else "Missing key",
            "Model": self.settings.model_name,
            "Music": f"{len(music_files)} files",
            "Audio Output": "Ready" if pygame.mixer.get_init() else "Standby",
        }

    def get_diagnostics_report(self) -> str:
        diagnostics = collect_runtime_diagnostics(self.settings)
        return format_runtime_diagnostics(diagnostics)

    # =========================
    # SPEECH OUTPUT
    # =========================
    def _maybe_speak(self, reply: AssistantReply, speak_response: bool) -> None:
        if speak_response and self.mouth:
            try:
                self.mouth.speak(reply.reply_text)
            except Exception as e:
                print(f"[TTS error]: {e}")