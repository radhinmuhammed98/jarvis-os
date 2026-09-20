"""
Voice Activity Detection (VAD) Subsystem
"""

from abc import ABC, abstractmethod
from voice.types import AudioChunk, AudioConfig

class BaseVAD(ABC):
    @abstractmethod
    def is_speech(self, chunk: AudioChunk) -> bool:
        pass


class SimpleVAD(BaseVAD):
    """Energy-based / flag-based Voice Activity Detector."""

    def __init__(self, config: AudioConfig):
        self.config = config

    def is_speech(self, chunk: AudioChunk) -> bool:
        # Check explicit flag first
        if chunk.is_speech:
            return True
        # If all zero bytes, it's silence
        if not chunk.data or all(b == 0 for b in chunk.data):
            return False
        # Calculate energy for PCM audio
        energy = sum(abs(b - 128) for b in chunk.data) / len(chunk.data)
        return energy > (self.config.vad_threshold * 10)
