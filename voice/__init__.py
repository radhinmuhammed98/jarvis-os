"""
JARVIS Voice Subsystem
"""

from voice.types import (
    AudioConfig, AudioChunk, TranscriptionResult, TTSChunk,
    VoiceState, VoiceStateMachine, BaseWakeWordDetector, MockWakeWordDetector
)
from voice.capture import BaseAudioCapture, MockAudioCapture
from voice.vad import BaseVAD, SimpleVAD
from voice.stt import BaseSTT, MockSTT
from voice.tts import BaseTTS, MockTTS
from voice.pipeline import VoicePipeline

__all__ = [
    "AudioConfig",
    "AudioChunk",
    "TranscriptionResult",
    "TTSChunk",
    "VoiceState",
    "VoiceStateMachine",
    "BaseWakeWordDetector",
    "MockWakeWordDetector",
    "BaseAudioCapture",
    "MockAudioCapture",
    "BaseVAD",
    "SimpleVAD",
    "BaseSTT",
    "MockSTT",
    "BaseTTS",
    "MockTTS",
    "VoicePipeline"
]
