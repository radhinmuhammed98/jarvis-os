"""
Conversation History and Memory Management for JARVIS Core
"""

from typing import List, Optional
from core.types import Message, Role

class ConversationContext:
    """Manages short-term conversation context, token trimming, and message history."""

    def __init__(self, max_messages: int = 20, system_instruction: str = "You are JARVIS OS, an intelligent, local, voice-first operating system assistant."):
        self.max_messages = max_messages
        self.system_instruction = system_instruction
        self._history: List[Message] = []

    def add_message(self, role: Role, content: str) -> Message:
        msg = Message(role=role, content=content)
        self._history.append(msg)
        self._trim_history()
        return msg

    def get_messages(self) -> List[Message]:
        return list(self._history)

    def clear(self):
        self._history.clear()

    def _trim_history(self):
        if len(self._history) > self.max_messages:
            self._history = self._history[-self.max_messages:]
