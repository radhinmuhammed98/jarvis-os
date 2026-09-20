"""
Audio Capture Abstraction for Microphone & Output Device Handling
Supports discovery, error recovery, and graceful hardware fallback.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
import time
from voice.types import AudioConfig, AudioChunk

logger = logging.getLogger("jarvis-audio-capture")


class BaseAudioCapture(ABC):
    """Abstract Microphone / Audio Capture Interface."""

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.is_running = False

    @abstractmethod
    def list_devices(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def initialize_audio(self) -> Dict[str, Any]:
        """Discover and select configured microphone and output devices."""
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
    """Mock Audio Capture for GUI-less / headless CI testing with failure simulation capabilities."""

    def __init__(self, config: Optional[AudioConfig] = None):
        super().__init__(config)
        self._mock_queue: List[AudioChunk] = []
        self.simulate_failure = False
        self.device_available = True
        self.active_input_device: Optional[Dict[str, Any]] = None
        self.active_output_device: Optional[Dict[str, Any]] = None

    def list_devices(self) -> List[Dict[str, Any]]:
        if not self.device_available:
            return []
        return [
            {"id": "default_mic", "name": "Default Microphone", "type": "input", "channels": 1, "default": True},
            {"id": "usb_mic_01", "name": "USB Audio Device", "type": "input", "channels": 1, "default": False},
            {"id": "default_speaker", "name": "Default Speaker", "type": "output", "channels": 2, "default": True}
        ]

    def initialize_audio(self) -> Dict[str, Any]:
        """Attempt to discover and initialize devices with retry logic."""
        logger.info("[AudioCapture] Initializing audio hardware discovery...")
        devices = self.list_devices()

        inputs = [d for d in devices if d.get("type") == "input"]
        outputs = [d for d in devices if d.get("type") == "output"]

        selected_input = None
        if self.config.input_device_id:
            selected_input = next((d for d in inputs if d["id"] == self.config.input_device_id), None)
        if not selected_input and inputs:
            selected_input = next((d for d in inputs if d.get("default")), inputs[0])

        selected_output = None
        if self.config.output_device_id:
            selected_output = next((d for d in outputs if d["id"] == self.config.output_device_id), None)
        if not selected_output and outputs:
            selected_output = next((d for d in outputs if d.get("default")), outputs[0])

        self.active_input_device = selected_input
        self.active_output_device = selected_output

        if not selected_input:
            logger.warning("[AudioCapture] No input microphone device found! Entering degraded silent mode.")

        return {
            "success": selected_input is not None,
            "input_device": selected_input,
            "output_device": selected_output,
            "available_devices_count": len(devices)
        }

    def start_stream(self) -> None:
        if self.simulate_failure:
            raise RuntimeError("Hardware audio stream initialization failed!")
        self.is_running = True

    def stop_stream(self) -> None:
        self.is_running = False

    def enqueue_mock_audio(self, pcm_bytes: bytes, is_speech: bool = True):
        self._mock_queue.append(AudioChunk(data=pcm_bytes, is_speech=is_speech))

    def read_chunk(self) -> AudioChunk:
        if self.simulate_failure:
            raise IOError("Microphone device disconnected unexpectedly")

        if not self.is_running or not self.active_input_device:
            return AudioChunk(data=b"\x00" * 1024, is_speech=False)

        if self._mock_queue:
            return self._mock_queue.pop(0)

        return AudioChunk(data=b"\x00" * 1024, is_speech=False)
