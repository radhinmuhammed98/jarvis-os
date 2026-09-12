"""
JARVIS Voice Pipeline Orchestrator (Milestone 08)
Connects Audio Capture -> VAD -> Streaming STT -> JARVIS Core -> Intent Engine -> Validation -> Tool / TTS.
Supports real-time speech barge-in/interruption.
STRICT RULE: Partial transcriptions NEVER trigger actions or intent evaluation.
"""

import logging
from typing import Dict, Any, Optional, Generator
from voice.types import AudioConfig, AudioChunk, TranscriptionResult, TTSChunk
from voice.capture import BaseAudioCapture, MockAudioCapture
from voice.vad import BaseVAD, SimpleVAD
from voice.stt import BaseSTT, MockSTT
from voice.tts import BaseTTS, MockTTS
from core.service import JarvisCore
from tools.executor import ToolExecutor

logger = logging.getLogger("jarvis-voice-pipeline")

class VoicePipeline:
    """Orchestrates streaming voice input, processing, JARVIS Core execution, and barge-in TTS."""

    def __init__(
        self,
        core: JarvisCore,
        tool_executor: Optional[ToolExecutor] = None,
        audio_capture: Optional[BaseAudioCapture] = None,
        vad: Optional[BaseVAD] = None,
        stt: Optional[BaseSTT] = None,
        tts: Optional[BaseTTS] = None,
        config: Optional[AudioConfig] = None
    ):
        self.config = config or AudioConfig()
        self.core = core
        self.tool_executor = tool_executor
        self.capture = audio_capture or MockAudioCapture(self.config)
        self.vad = vad or SimpleVAD(self.config)
        self.stt = stt or MockSTT()
        self.tts = tts or MockTTS()

    def handle_audio_chunk(self, chunk: AudioChunk) -> Dict[str, Any]:
        """
        Processes audio chunk.
        If user speaks while TTS is active, interrupts TTS immediately (barge-in).
        Only finalized complete transcriptions are dispatched to JARVIS Core.
        """
        is_speech = self.vad.is_speech(chunk)

        # Barge-in check: Interrupt TTS if user speaks
        if is_speech and self.tts.is_speaking:
            logger.info("[VoicePipeline] User barge-in detected! Interrupting TTS playback.")
            self.tts.stop()

        if not is_speech:
            # Silence detected -> check if we need to finalize an active utterance
            final_stt = self.stt.finalize_utterance()
            if final_stt and final_stt.is_final:
                return self._process_final_utterance(final_stt.text)
            return {"status": "silence", "transcription": None, "core_response": None}

        # User is speaking -> process audio chunk through STT
        stt_result = self.stt.process_audio_chunk(chunk)
        if not stt_result:
            return {"status": "listening", "transcription": None, "core_response": None}

        if not stt_result.is_final:
            logger.debug(f"[VoicePipeline] Partial transcription: '{stt_result.text}' (NO action trigger)")
            return {
                "status": "partial_transcription",
                "transcription": stt_result.text,
                "core_response": None,
                "executed": False
            }

        # Finalized transcription -> Dispatch to JARVIS Core
        return self._process_final_utterance(stt_result.text)

    def _process_final_utterance(self, text: str) -> Dict[str, Any]:
        logger.info(f"[VoicePipeline] Finalized utterance: '{text}' -> Dispatching to JARVIS Core")

        # Core process message (Intent Engine -> Validation Gate)
        core_res = self.core.process_message(text)

        # Execute validated action proposal if present AND executor available
        tool_result = None
        if core_res.get("action_proposal") and core_res["action_proposal"].validated and self.tool_executor:
            tool_result = self.tool_executor.execute_proposal(core_res["action_proposal"])
            core_res["executed"] = tool_result.success

        # Speak response via TTS
        tts_text = core_res.get("text", "")
        tts_chunks = list(self.tts.speak_stream(tts_text)) if tts_text else []

        return {
            "status": "utterance_processed",
            "transcription": text,
            "core_response": core_res,
            "tool_result": tool_result,
            "tts_output": tts_chunks
        }
