"""
Audio Capture Abstraction for Microphone Input
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from voice.types import AudioConfig, AudioChunk

class BaseAudioCapture(ABC):
    """Abstract Microphone / Audio Capture Interface."""

    @abstractmethod
    def list_devices(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def start_stream(self) -> None:
        pass

    @abstractmethod
    def stop_stream(self) -> None:
        pass

    @abstractmethod
    def read_chunk(self) -> AudioChunk:
        pass


class MockAudioCapture(BaseAudioCapture):
    """Mock Audio Capture for GUI-less / headless CI testing."""

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.is_running = False
        self._mock_queue: List[AudioChunk] = []

    def list_devices(self) -> List[Dict[str, Any]]:
        return [
            {"id": "default_mic", "name": "Default Microphone", "type": "input"},
            {"id": "usb_mic_01", "name": "USB Audio Device", "type": "input"}
        ]

    def start_stream(self) -> None:
        self.is_running = True

    def stop_stream(self) -> None:
        self.is_running = False

    def enqueue_mock_audio(self, pcm_bytes: bytes, is_speech: bool = True):
        self._mock_queue.append(AudioChunk(data=pcm_bytes, is_speech=is_speech))

    def read_chunk(self) -> AudioChunk:
        if self._mock_queue:
            return self._mock_queue.pop(0)
        return AudioChunk(data=b"\x00" * 1024, is_speech=False)
