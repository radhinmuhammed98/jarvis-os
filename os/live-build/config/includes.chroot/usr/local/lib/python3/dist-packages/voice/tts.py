"""
Text-To-Speech (TTS) Abstraction & Mock Provider with Interruption (Barge-In)
"""

from abc import ABC, abstractmethod
from typing import Generator, Optional
import time
from voice.types import TTSChunk

class BaseTTS(ABC):
    @abstractmethod
    def speak_stream(self, text: str) -> Generator[TTSChunk, None, None]:
        pass

    @abstractmethod
    def stop(self) -> None:
        """Interrupts current speech playback immediately."""
        pass


class MockTTS(BaseTTS):
    """Mock TTS Engine with interruption support."""

    def __init__(self):
        self._is_speaking = False
        self._interrupted = False

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    @property
    def was_interrupted(self) -> bool:
        return self._interrupted

    def stop(self) -> None:
        self._interrupted = True
        self._is_speaking = False

    def speak_stream(self, text: str) -> Generator[TTSChunk, None, None]:
        self._is_speaking = True
        self._interrupted = False

        words = text.split()
        for i, w in enumerate(words):
            if self._interrupted:
                break
            is_last = (i == len(words) - 1)
            fake_audio = f"AUDIO_DATA[{w}]".encode("utf-8")
            yield TTSChunk(audio_data=fake_audio, text=w, is_final=is_last)

        self._is_speaking = False
