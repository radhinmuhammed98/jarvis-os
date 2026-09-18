"""
JARVIS Voice Pipeline Data Types, State Machine, and Wake Word Abstractions
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from abc import ABC, abstractmethod
import time
import logging

logger = logging.getLogger("jarvis-voice-types")


class VoiceState(Enum):
    OFF = "OFF"
    INITIALIZING = "INITIALIZING"
    IDLE = "IDLE"
    WAKE_DETECTED = "WAKE_DETECTED"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"


# Valid state transitions matrix
VALID_TRANSITIONS: Dict[VoiceState, List[VoiceState]] = {
    VoiceState.OFF: [VoiceState.INITIALIZING, VoiceState.ERROR],
    VoiceState.INITIALIZING: [VoiceState.IDLE, VoiceState.ERROR],
    VoiceState.IDLE: [VoiceState.WAKE_DETECTED, VoiceState.LISTENING, VoiceState.OFF, VoiceState.ERROR],
    VoiceState.WAKE_DETECTED: [VoiceState.LISTENING, VoiceState.IDLE, VoiceState.ERROR],
    VoiceState.LISTENING: [VoiceState.PROCESSING, VoiceState.IDLE, VoiceState.INTERRUPTED, VoiceState.ERROR],
    VoiceState.PROCESSING: [VoiceState.SPEAKING, VoiceState.IDLE, VoiceState.LISTENING, VoiceState.ERROR],
    VoiceState.SPEAKING: [VoiceState.IDLE, VoiceState.INTERRUPTED, VoiceState.LISTENING, VoiceState.ERROR],
    VoiceState.INTERRUPTED: [VoiceState.LISTENING, VoiceState.PROCESSING, VoiceState.IDLE, VoiceState.ERROR],
    VoiceState.ERROR: [VoiceState.INITIALIZING, VoiceState.IDLE, VoiceState.OFF]
}


class VoiceStateMachine:
    """Explicit Voice Pipeline State Machine with transition validation."""

    def __init__(self, initial_state: VoiceState = VoiceState.OFF):
        self._state = initial_state
        self._history: List[VoiceState] = [initial_state]
        self._on_transition_callbacks: List[Callable[[VoiceState, VoiceState], None]] = []

    @property
    def current_state(self) -> VoiceState:
        return self._state

    @property
    def history(self) -> List[VoiceState]:
        return list(self._history)

    def add_transition_callback(self, callback: Callable[[VoiceState, VoiceState], None]):
        self._on_transition_callbacks.append(callback)

    def transition_to(self, new_state: VoiceState) -> bool:
        """Attempt to transition to new_state. Returns True if valid, False if rejected."""
        if new_state == self._state:
            return True

        allowed = VALID_TRANSITIONS.get(self._state, [])
        if new_state not in allowed:
            logger.warning(
                f"[VoiceStateMachine] Invalid state transition rejected: {self._state.value} -> {new_state.value}"
            )
            return False

        old_state = self._state
        self._state = new_state
        self._history.append(new_state)
        logger.info(f"[VoiceStateMachine] State transition: {old_state.value} -> {new_state.value}")

        for cb in self._on_transition_callbacks:
            try:
                cb(old_state, new_state)
            except Exception as e:
                logger.error(f"[VoiceStateMachine] Transition callback error: {e}")

        return True


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    input_device_id: Optional[str] = None
    output_device_id: Optional[str] = None
    vad_threshold: float = 0.5
    silence_duration_ms: float = 500.0
    wake_phrase: str = "JARVIS"
    wake_sensitivity: float = 0.7
    listening_timeout: float = 5.0
    follow_up_mode: bool = True
    audio_retry_count: int = 3
    audio_retry_delay: float = 1.0


@dataclass
class AudioChunk:
    data: bytes
    timestamp: float = field(default_factory=time.time)
    is_speech: bool = False


@dataclass
class TranscriptionResult:
    text: str
    is_final: bool = False
    confidence: float = 1.0


@dataclass
class TTSChunk:
    audio_data: bytes
    text: str
    is_final: bool = False


class BaseWakeWordDetector(ABC):
    """Abstract Wake-Word Detector Interface."""

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.is_active = False

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def process_chunk(self, chunk: AudioChunk) -> bool:
        """Process an audio chunk in low-power idle mode. Returns True if wake phrase detected."""
        pass


class MockWakeWordDetector(BaseWakeWordDetector):
    """Mock Wake Word Detector for hardware-less testing."""

    def __init__(self, config: Optional[AudioConfig] = None):
        super().__init__(config)
        self._triggered = False
        self._mock_keywords: List[str] = []

    def start(self) -> None:
        self.is_active = True

    def stop(self) -> None:
        self.is_active = False

    def trigger_wake(self):
        """Simulate wake word event."""
        self._triggered = True

    def process_chunk(self, chunk: AudioChunk) -> bool:
        if not self.is_active:
            return False

        if self._triggered:
            self._triggered = False
            return True

        # Check if text audio simulation payload contains wake phrase
        if chunk.data:
            try:
                decoded = chunk.data.decode("utf-8", errors="ignore")
                if self.config.wake_phrase.lower() in decoded.lower():
                    return True
            except Exception:
                pass

        return False
