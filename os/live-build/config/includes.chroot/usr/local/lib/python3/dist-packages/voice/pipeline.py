"""
JARVIS Voice Subsystem Orchestrator (Milestone 09)
Always-On Voice Service + Wake Word Detector + Voice Pipeline + State Machine + Boot Integration.

Pipeline Flow:
Boot -> Systemd -> Voice Service -> Wake Word Detector -> Voice Pipeline -> STT -> Core -> Intent -> Validation -> Security/Tools -> TTS -> Idle
"""

import logging
import time
from typing import Dict, Any, Optional, List, Generator
from voice.types import (
    AudioConfig, AudioChunk, TranscriptionResult, TTSChunk,
    VoiceState, VoiceStateMachine, BaseWakeWordDetector, MockWakeWordDetector
)
from voice.capture import BaseAudioCapture, MockAudioCapture
from voice.vad import BaseVAD, SimpleVAD
from voice.stt import BaseSTT, MockSTT
from voice.tts import BaseTTS, MockTTS
from core.service import JarvisCore
from tools.executor import ToolExecutor

logger = logging.getLogger("jarvis-voice-pipeline")


class VoicePipeline:
    """
    Orchestrates always-on voice interaction:
    - Audio initialization & device discovery
    - Low-power wake word detection in IDLE
    - Explicit state machine transitions
    - Real-time speech barge-in TTS interruption
    - Listening timeout & follow-up conversation management
    - Strict security guarantees: wake word alone triggers no actions, partial STT never executes actions.
    """

    def __init__(
        self,
        core: JarvisCore,
        tool_executor: Optional[ToolExecutor] = None,
        audio_capture: Optional[BaseAudioCapture] = None,
        wake_detector: Optional[BaseWakeWordDetector] = None,
        vad: Optional[BaseVAD] = None,
        stt: Optional[BaseSTT] = None,
        tts: Optional[BaseTTS] = None,
        config: Optional[AudioConfig] = None,
        start_in_listening: bool = True
    ):
        self.config = config or AudioConfig()
        self.core = core
        self.tool_executor = tool_executor
        self.capture = audio_capture or MockAudioCapture(self.config)
        self.wake_detector = wake_detector or MockWakeWordDetector(self.config)
        self.vad = vad or SimpleVAD(self.config)
        self.stt = stt or MockSTT()
        self.tts = tts or MockTTS()

        self.state_machine = VoiceStateMachine(VoiceState.OFF)
        self.last_speech_time: Optional[float] = None
        self._initialize_subsystem(start_in_listening=start_in_listening)

    def _initialize_subsystem(self, start_in_listening: bool = True):
        """Initializes audio devices and transitions to IDLE or LISTENING state."""
        self.state_machine.transition_to(VoiceState.INITIALIZING)
        init_res = self.capture.initialize_audio()
        if not init_res.get("success"):
            logger.warning("[VoicePipeline] Audio capture initialization incomplete or running degraded.")

        self.wake_detector.start()
        self.capture.start_stream()

        if start_in_listening:
            self.state_machine.transition_to(VoiceState.IDLE)
            self.state_machine.transition_to(VoiceState.WAKE_DETECTED)
            self.state_machine.transition_to(VoiceState.LISTENING)
            self.last_speech_time = time.time()
        else:
            self.state_machine.transition_to(VoiceState.IDLE)

        logger.info(f"[VoicePipeline] JARVIS Voice Subsystem initialized in {self.state_machine.current_state.value} state.")

    def handle_audio_chunk(self, chunk: AudioChunk) -> Dict[str, Any]:
        """
        Primary entry point for processing an audio chunk through the state machine.
        Handles wake detection, listening, barge-in, timeouts, and action dispatch.
        """
        current_state = self.state_machine.current_state

        # Check speech activity via VAD
        is_speech = self.vad.is_speech(chunk)

        # 1. Barge-In Interruption check (when speaking or when TTS is active)
        if (current_state == VoiceState.SPEAKING or self.tts.is_speaking) and is_speech:
            logger.info("[VoicePipeline] User barge-in detected during TTS speech! Interrupting playback.")
            self.tts.stop()
            if self.state_machine.current_state == VoiceState.SPEAKING:
                self.state_machine.transition_to(VoiceState.INTERRUPTED)
                self.state_machine.transition_to(VoiceState.LISTENING)
            self.last_speech_time = time.time()

        # Update current state reference after barge-in processing
        current_state = self.state_machine.current_state

        # 2. State: IDLE -> Low-power wake word detection
        if current_state == VoiceState.IDLE:
            if self.wake_detector.process_chunk(chunk):
                logger.info(f"[VoicePipeline] Wake phrase '{self.config.wake_phrase}' detected!")
                self.state_machine.transition_to(VoiceState.WAKE_DETECTED)
                self.state_machine.transition_to(VoiceState.LISTENING)
                self.last_speech_time = time.time()
                return {
                    "status": "wake_detected",
                    "state": self.state_machine.current_state.value,
                    "transcription": None,
                    "core_response": None,
                    "action_executed": False
                }
            return {
                "status": "idle",
                "state": self.state_machine.current_state.value,
                "transcription": None,
                "core_response": None,
                "action_executed": False
            }

        # 3. State: LISTENING / WAKE_DETECTED
        if current_state in (VoiceState.LISTENING, VoiceState.WAKE_DETECTED):
            if is_speech:
                self.last_speech_time = time.time()
                stt_res = self.stt.process_audio_chunk(chunk)
                if stt_res:
                    if stt_res.is_final:
                        return self._process_final_utterance(stt_res.text)
                    else:
                        logger.debug(f"[VoicePipeline] Partial STT: '{stt_res.text}' (NO action evaluation)")
                        return {
                            "status": "partial_transcription",
                            "state": self.state_machine.current_state.value,
                            "transcription": stt_res.text,
                            "core_response": None,
                            "action_executed": False,
                            "executed": False
                        }
                return {
                    "status": "listening",
                    "state": self.state_machine.current_state.value,
                    "transcription": None,
                    "core_response": None,
                    "action_executed": False
                }
            else:
                # Silence detected during LISTENING
                final_stt = self.stt.finalize_utterance()
                if final_stt and final_stt.text:
                    return self._process_final_utterance(final_stt.text)

                # Check for listening timeout
                if self.last_speech_time and (time.time() - self.last_speech_time) > self.config.listening_timeout:
                    logger.info("[VoicePipeline] Listening timeout reached. Returning to IDLE.")
                    self.state_machine.transition_to(VoiceState.IDLE)
                    return {
                        "status": "timeout",
                        "state": self.state_machine.current_state.value,
                        "transcription": None,
                        "core_response": None,
                        "action_executed": False
                    }

                return {
                    "status": "silence",
                    "state": self.state_machine.current_state.value,
                    "transcription": None,
                    "core_response": None,
                    "action_executed": False
                }

        return {
            "status": "processing",
            "state": self.state_machine.current_state.value,
            "transcription": None,
            "core_response": None,
            "action_executed": False
        }

    def _process_final_utterance(self, text: str) -> Dict[str, Any]:
        """Dispatches a complete finalized utterance through Core -> Intent Engine -> Validation Gate -> Tools -> TTS."""
        logger.info(f"[VoicePipeline] Processing finalized utterance: '{text}'")
        self.state_machine.transition_to(VoiceState.PROCESSING)

        # Dispatch message through JARVIS Core (Intent Engine + Validation Gate)
        core_res = self.core.process_message(text)

        # Execute validated action proposal if present and executor attached
        tool_result = None
        action_executed = False
        if core_res.get("action_proposal") and core_res["action_proposal"].validated and self.tool_executor:
            tool_result = self.tool_executor.execute_proposal(core_res["action_proposal"])
            action_executed = tool_result.success
            core_res["executed"] = action_executed

        # Speak output response via TTS
        tts_text = core_res.get("text", "")
        tts_chunks = []
        if tts_text:
            self.state_machine.transition_to(VoiceState.SPEAKING)
            tts_chunks = list(self.tts.speak_stream(tts_text))

        # Handle post-response state (Follow-up conversation or IDLE)
        if self.config.follow_up_mode and self.state_machine.current_state in (VoiceState.SPEAKING, VoiceState.PROCESSING):
            logger.info("[VoicePipeline] Follow-up conversation enabled. Entering LISTENING state.")
            self.state_machine.transition_to(VoiceState.LISTENING)
            self.last_speech_time = time.time()
        else:
            self.state_machine.transition_to(VoiceState.IDLE)

        return {
            "status": "utterance_processed",
            "state": self.state_machine.current_state.value,
            "transcription": text,
            "core_response": core_res,
            "tool_result": tool_result,
            "action_executed": action_executed,
            "tts_output": tts_chunks
        }

    def stop(self):
        """Shutdown voice subsystem safely."""
        logger.info("[VoicePipeline] Shutting down JARVIS Voice Subsystem...")
        self.wake_detector.stop()
        self.capture.stop_stream()
        self.state_machine.transition_to(VoiceState.OFF)


def run_voice_service():
    """Background entrypoint for systemd service execution."""
    from core.brain import MockBrain
    from core.config import CoreConfig
    from agent.intent_engine import IntentEngine
    from agent.validation_gate import ValidationGate

    logger.info("[VoiceService] Starting JARVIS Voice Background Service...")
    core = JarvisCore()
    pipeline = VoicePipeline(core=core)

    try:
        while True:
            chunk = pipeline.capture.read_chunk()
            pipeline.handle_audio_chunk(chunk)
            time.sleep(0.05)
    except KeyboardInterrupt:
        logger.info("[VoiceService] Interrupted by signal. Stopping service.")
    finally:
        pipeline.stop()


if __name__ == "__main__":
    run_voice_service()
