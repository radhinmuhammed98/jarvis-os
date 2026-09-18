"""
Milestone 08 & 09 Comprehensive Test Suite:
Always-On Voice Subsystem, Wake Word Detection, Explicit State Machine,
Streaming STT, Barge-In Interruption, Listening Timeout, Follow-Up Mode,
Audio Hardware Error Recovery, and Intent Pipeline Security Integration.
"""

import pytest
import time
from voice import (
    VoicePipeline,
    MockAudioCapture,
    SimpleVAD,
    MockSTT,
    MockTTS,
    AudioConfig,
    AudioChunk,
    VoiceState,
    VoiceStateMachine,
    MockWakeWordDetector
)
from core.service import JarvisCore
from core.config import CoreConfig
from system.computer import MockComputerController
from tools import ToolRegistry, PermissionPolicy, AuditLogger, ToolExecutor, AppLaunchTool
from core.types import IntentCategory


@pytest.fixture
def voice_pipeline_env():
    core = JarvisCore(CoreConfig(provider="mock"))
    controller = MockComputerController()
    registry = ToolRegistry()
    registry.register_tool(AppLaunchTool(controller))

    policy = PermissionPolicy(granted_permissions=["app:launch"])
    audit = AuditLogger()
    executor = ToolExecutor(registry, policy, audit)

    config = AudioConfig(wake_phrase="JARVIS", listening_timeout=1.0, follow_up_mode=True)
    capture = MockAudioCapture(config)
    wake_detector = MockWakeWordDetector(config)
    vad = SimpleVAD(config)
    stt = MockSTT()
    tts = MockTTS()

    pipeline = VoicePipeline(
        core=core,
        tool_executor=executor,
        audio_capture=capture,
        wake_detector=wake_detector,
        vad=vad,
        stt=stt,
        tts=tts,
        config=config,
        start_in_listening=True
    )
    return pipeline, controller, stt, tts, capture, wake_detector


# --- Milestone 08 Core Requirements ---

def test_silence_handling(voice_pipeline_env):
    pipeline, controller, stt, tts, capture, wake = voice_pipeline_env
    chunk = AudioChunk(data=b"\x00" * 1024, is_speech=False)
    res = pipeline.handle_audio_chunk(chunk)
    assert res["status"] in ("silence", "idle")
    assert res["core_response"] is None


def test_partial_transcription_does_not_trigger_action(voice_pipeline_env):
    pipeline, controller, stt, tts, capture, wake = voice_pipeline_env
    stt.simulate_speech_input("Open Chrome")

    # First audio chunk -> emits partial "Open"
    chunk = AudioChunk(data=b"\xFF" * 1024, is_speech=True)
    res = pipeline.handle_audio_chunk(chunk)

    assert res["status"] == "partial_transcription"
    assert res["transcription"] == "Open"
    assert res["core_response"] is None
    assert len(controller.running_apps) == 0


def test_finalized_transcription_action_request(voice_pipeline_env):
    """Proves 'Open Chrome' -> Finalized STT -> Intent Engine -> Validation Gate -> Permission -> AppLaunchTool."""
    pipeline, controller, stt, tts, capture, wake = voice_pipeline_env
    stt.simulate_speech_input("Open Chrome.")

    chunk_speech = AudioChunk(data=b"\xFF" * 1024, is_speech=True)
    pipeline.handle_audio_chunk(chunk_speech)

    chunk_silence = AudioChunk(data=b"\x00" * 1024, is_speech=False)
    res = pipeline.handle_audio_chunk(chunk_silence)

    assert res["status"] == "utterance_processed"
    assert res["transcription"] == "Open Chrome."
    assert res["core_response"]["intent"].category == IntentCategory.ACTION_REQUEST
    assert res["core_response"]["executed"] is True
    assert controller.running_apps["chrome"] is True


def test_conversation_without_action(voice_pipeline_env):
    """Proves 'Chrome is really slow today' -> Finalized STT -> Conversation Path -> 0 computer action."""
    pipeline, controller, stt, tts, capture, wake = voice_pipeline_env
    stt.simulate_speech_input("Chrome is really slow today.")

    chunk_speech = AudioChunk(data=b"\xFF" * 1024, is_speech=True)
    pipeline.handle_audio_chunk(chunk_speech)

    chunk_silence = AudioChunk(data=b"\x00" * 1024, is_speech=False)
    res = pipeline.handle_audio_chunk(chunk_silence)

    assert res["status"] == "utterance_processed"
    assert res["core_response"]["intent"].category != IntentCategory.ACTION_REQUEST
    assert len(controller.running_apps) == 0


def test_barge_in_interruption(voice_pipeline_env):
    """Proves user speech during TTS playback interrupts TTS immediately."""
    pipeline, controller, stt, tts, capture, wake = voice_pipeline_env

    tts._is_speaking = True
    speech_chunk = AudioChunk(data=b"\xFF" * 1024, is_speech=True)
    pipeline.handle_audio_chunk(speech_chunk)

    assert tts.was_interrupted is True
    assert tts.is_speaking is False


# --- Milestone 09 Always-On Voice & Wake Word Requirements ---

def test_wake_word_detection(voice_pipeline_env):
    """Test wake word detection transitions state from IDLE to LISTENING."""
    pipeline, controller, stt, tts, capture, wake = voice_pipeline_env

    # Explicitly set to IDLE
    pipeline.state_machine.transition_to(VoiceState.IDLE)
    assert pipeline.state_machine.current_state == VoiceState.IDLE

    # Trigger wake word
    wake.trigger_wake()
    chunk = AudioChunk(data=b"\x00" * 1024, is_speech=False)
    res = pipeline.handle_audio_chunk(chunk)

    assert res["status"] == "wake_detected"
    assert pipeline.state_machine.current_state == VoiceState.LISTENING


def test_wake_word_alone_triggers_no_action(voice_pipeline_env):
    """Wake word alone activates session but MUST NOT execute any system tools or actions."""
    pipeline, controller, stt, tts, capture, wake = voice_pipeline_env

    pipeline.state_machine.transition_to(VoiceState.IDLE)
    wake.trigger_wake()
    res = pipeline.handle_audio_chunk(AudioChunk(data=b"\x00" * 1024, is_speech=False))

    assert res["status"] == "wake_detected"
    assert res["action_executed"] is False
    assert len(controller.running_apps) == 0


def test_wake_word_followed_by_complete_command(voice_pipeline_env):
    """Wake word -> LISTENING -> Spoken command -> Validated computer action execution."""
    pipeline, controller, stt, tts, capture, wake = voice_pipeline_env

    # Start in IDLE
    pipeline.state_machine.transition_to(VoiceState.IDLE)

    # 1. Wake detection
    wake.trigger_wake()
    pipeline.handle_audio_chunk(AudioChunk(data=b"\x00" * 1024, is_speech=False))

    # 2. Spoken command
    stt.simulate_speech_input("Open Chrome.")
    pipeline.handle_audio_chunk(AudioChunk(data=b"\xFF" * 1024, is_speech=True))
    res = pipeline.handle_audio_chunk(AudioChunk(data=b"\x00" * 1024, is_speech=False))

    assert res["status"] == "utterance_processed"
    assert controller.running_apps.get("chrome") is True


def test_listening_timeout(voice_pipeline_env):
    """In LISTENING state, prolonged silence causes timeout and returns system to IDLE."""
    pipeline, controller, stt, tts, capture, wake = voice_pipeline_env

    pipeline.state_machine.transition_to(VoiceState.LISTENING)
    pipeline.last_speech_time = time.time() - 2.0  # Expire 1.0s timeout

    silence_chunk = AudioChunk(data=b"\x00" * 1024, is_speech=False)
    res = pipeline.handle_audio_chunk(silence_chunk)

    assert res["status"] == "timeout"
    assert pipeline.state_machine.current_state == VoiceState.IDLE


def test_follow_up_conversation(voice_pipeline_env):
    """In follow-up mode, after completing a command, pipeline remains in LISTENING mode for follow-up."""
    pipeline, controller, stt, tts, capture, wake = voice_pipeline_env

    stt.simulate_speech_input("Open Chrome.")
    pipeline.handle_audio_chunk(AudioChunk(data=b"\xFF" * 1024, is_speech=True))
    res1 = pipeline.handle_audio_chunk(AudioChunk(data=b"\x00" * 1024, is_speech=False))

    assert res1["status"] == "utterance_processed"
    assert pipeline.state_machine.current_state == VoiceState.LISTENING

    # Send follow-up command
    stt.simulate_speech_input("Chrome is slow today.")
    pipeline.handle_audio_chunk(AudioChunk(data=b"\xFF" * 1024, is_speech=True))
    res2 = pipeline.handle_audio_chunk(AudioChunk(data=b"\x00" * 1024, is_speech=False))

    assert res2["status"] == "utterance_processed"


def test_state_machine_transitions():
    """Verify valid state transitions and rejection of invalid state transitions."""
    sm = VoiceStateMachine(VoiceState.OFF)

    assert sm.transition_to(VoiceState.INITIALIZING) is True
    assert sm.transition_to(VoiceState.IDLE) is True
    assert sm.transition_to(VoiceState.WAKE_DETECTED) is True
    assert sm.transition_to(VoiceState.LISTENING) is True

    # Invalid direct jump: LISTENING -> INITIALIZING should be rejected
    assert sm.transition_to(VoiceState.INITIALIZING) is False
    assert sm.current_state == VoiceState.LISTENING


def test_audio_device_discovery_and_failure_recovery(voice_pipeline_env):
    """Verify device discovery and graceful handling of missing or disconnected microphone."""
    pipeline, controller, stt, tts, capture, wake = voice_pipeline_env

    # Simulate hardware unavailability
    capture.device_available = False
    init_res = capture.initialize_audio()

    assert init_res["success"] is False
    assert init_res["input_device"] is None

    # Reading chunk when capture device is missing should yield silent chunks safely without crash
    chunk = capture.read_chunk()
    assert chunk.is_speech is False
