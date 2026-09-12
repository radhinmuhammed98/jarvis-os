"""
Milestone 08 Test Suite: Voice Pipeline, Streaming STT, Barge-In Interruption, and Intent Pipeline Integration
"""

import pytest
from voice import (
    VoicePipeline,
    MockAudioCapture,
    SimpleVAD,
    MockSTT,
    MockTTS,
    AudioConfig,
    AudioChunk
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

    capture = MockAudioCapture()
    vad = SimpleVAD(AudioConfig())
    stt = MockSTT()
    tts = MockTTS()

    pipeline = VoicePipeline(
        core=core,
        tool_executor=executor,
        audio_capture=capture,
        vad=vad,
        stt=stt,
        tts=tts
    )
    return pipeline, controller, stt, tts, capture

def test_silence_handling(voice_pipeline_env):
    pipeline, controller, stt, tts, capture = voice_pipeline_env
    chunk = AudioChunk(data=b"\x00" * 1024, is_speech=False)
    res = pipeline.handle_audio_chunk(chunk)
    assert res["status"] == "silence"
    assert res["core_response"] is None

def test_partial_transcription_does_not_trigger_action(voice_pipeline_env):
    pipeline, controller, stt, tts, capture = voice_pipeline_env
    stt.simulate_speech_input("Open Chrome")

    # First audio chunk -> emits partial "Open"
    chunk = AudioChunk(data=b"\xFF" * 1024, is_speech=True)
    res = pipeline.handle_audio_chunk(chunk)

    assert res["status"] == "partial_transcription"
    assert res["transcription"] == "Open"
    assert res["core_response"] is None
    assert len(controller.running_apps) == 0

def test_finalized_transcription_action_request(voice_pipeline_env):
    """
    Proves:
    'Open Chrome' -> Finalized STT -> Intent Engine -> Validation -> Permission -> AppLaunchTool
    """
    pipeline, controller, stt, tts, capture = voice_pipeline_env
    stt.simulate_speech_input("Open Chrome.")

    # Speech chunk followed by silence to finalize
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
    """
    Proves:
    'Chrome is really slow today' -> Finalized STT -> Conversation Path -> 0 computer action
    """
    pipeline, controller, stt, tts, capture = voice_pipeline_env
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
    pipeline, controller, stt, tts, capture = voice_pipeline_env

    # Start TTS speech stream
    tts._is_speaking = True

    # User starts speaking -> speech chunk arrives
    speech_chunk = AudioChunk(data=b"\xFF" * 1024, is_speech=True)
    pipeline.handle_audio_chunk(speech_chunk)

    assert tts.was_interrupted is True
    assert tts.is_speaking is False
