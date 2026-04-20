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
            self.brain = Brain(api_key=settings.gemini_api_key, model_name=settings.model_name)

    def ensure_music_ready(self) -> tuple[bool, str | None]:
        if pygame.mixer.get_init():
            return True, None

        try:
            pygame.mixer.init()
            return True, None
        except pygame.error as e:
            return False, f"Không thể khởi tạo âm thanh phát nhạc: {e}"

    def process_text(self, user_text: str, *, speak_response: bool = False) -> AssistantReply:
        clean_text = user_text.strip()
        if not clean_text:
            return AssistantReply(
                user_text=user_text,
                reply_text="Mình chưa nhận được nội dung nào.",
                intent="empty",
            )

        command = parse_rule_command(clean_text)
        if command:
            intent = str(command["intent"])

            if intent == "exit":
                self.skills.stop_music()
                reply = AssistantReply(
                    user_text=clean_text,
                    reply_text="Tạm biệt bạn, hẹn gặp lại!",
                    intent=intent,
                    should_exit=True,
                )
                self._maybe_speak(reply, speak_response)
                return reply

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

            if intent == "play_music":
                ready, audio_message = self.ensure_music_ready()
                if not ready:
                    reply = AssistantReply(
                        user_text=clean_text,
                        reply_text=audio_message or "Không thể phát nhạc lúc này.",
                        intent=intent,
                        status_text=audio_message,
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

            if intent == "weather":
                weather_info = self.skills.get_weather(str(command["city"]))
                reply = AssistantReply(
                    user_text=clean_text,
                    reply_text=weather_info,
                    intent=intent,
                )
                self._maybe_speak(reply, speak_response)
                return reply

        if not self.brain:
            reply = AssistantReply(
                user_text=clean_text,
                reply_text="Chưa cấu hình GEMINI_API_KEY nên mình chưa thể trò chuyện bằng AI.",
                intent="chat_unavailable",
            )
            self._maybe_speak(reply, speak_response)
            return reply

        ai_response = self.brain.think(clean_text)
        reply = AssistantReply(
            user_text=clean_text,
            reply_text=ai_response,
            intent="chat",
        )
        self._maybe_speak(reply, speak_response)
        return reply

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

    def _maybe_speak(self, reply: AssistantReply, speak_response: bool) -> None:
        if speak_response:
            self.mouth.speak(reply.reply_text)
