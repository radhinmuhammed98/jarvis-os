"""
JARVIS Voice Pipeline Data Types
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import time

@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    input_device_id: Optional[str] = None
    output_device_id: Optional[str] = None
    vad_threshold: float = 0.5
    silence_duration_ms: float = 500.0

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
