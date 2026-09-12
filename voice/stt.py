"""
Speech-To-Text (STT) Abstraction Interface & Mock Provider
"""

from abc import ABC, abstractmethod
from typing import List, Generator, Optional
from voice.types import AudioChunk, TranscriptionResult

class BaseSTT(ABC):
    @abstractmethod
    def process_audio_chunk(self, chunk: AudioChunk) -> Optional[TranscriptionResult]:
        """
        Process audio chunk.
        Yields partial transcriptions or finalized transcription result.
        """
        pass

    @abstractmethod
    def finalize_utterance(self) -> Optional[TranscriptionResult]:
        pass


class MockSTT(BaseSTT):
    """Mock STT Provider for local testing."""

    def __init__(self):
        self._buffer_text = ""
        self._speech_count = 0

    def simulate_speech_input(self, text: str):
        self._buffer_text = text
        self._speech_count = 0

    def process_audio_chunk(self, chunk: AudioChunk) -> Optional[TranscriptionResult]:
        if not chunk.is_speech or not self._buffer_text:
            return None

        self._speech_count += 1
        words = self._buffer_text.split()

        if self._speech_count == 1 and len(words) > 1:
            partial_text = words[0]
            return TranscriptionResult(text=partial_text, is_final=False, confidence=0.8)

        return self.finalize_utterance()

    def finalize_utterance(self) -> Optional[TranscriptionResult]:
        if not self._buffer_text:
            return None
        final_text = self._buffer_text
        self._buffer_text = ""
        self._speech_count = 0
        return TranscriptionResult(text=final_text, is_final=True, confidence=0.98)
