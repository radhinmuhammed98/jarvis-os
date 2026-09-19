import pytest
from core.types import Role, Message
from core.brain import BaseBrain
from core.providers.mock import MockBrain
from core.providers.ollama import OllamaBrain
from core.context import ConversationContext
from core.config import CoreConfig
from core.service import JarvisCore

def test_mock_brain_generation():
    brain = MockBrain()
    msg = Message(role=Role.USER, content="Hello JARVIS")
    resp = brain.generate_response([msg])
    assert "Received 'Hello JARVIS'" in resp.text
    assert resp.is_final is True

def test_conversation_context_trimming():
    ctx = ConversationContext(max_messages=3)
    for i in range(5):
        ctx.add_message(Role.USER, f"Msg {i}")
    msgs = ctx.get_messages()
    assert len(msgs) == 3
    assert msgs[0].content == "Msg 2"
    assert msgs[-1].content == "Msg 4"

def test_jarvis_core_service_mock_process():
    config = CoreConfig(provider="mock", model_name="mock-test")
    core = JarvisCore(config)
    res = core.process_message("Open Chrome.")
    assert "text" in res
    assert res["executed"] is False
    assert res["action_proposal"] is not None
    assert res["action_proposal"].target.lower() == "chrome"

def test_jarvis_core_stream_process():
    config = CoreConfig(provider="mock", model_name="mock-test")
    core = JarvisCore(config)
    chunks = list(core.process_message_stream("Hello"))
    assert len(chunks) > 0
    assert chunks[-1].is_final is True
    assert chunks[-1].intent is not None

def test_ollama_brain_fallback():
    # Invalid host should gracefully fail and yield error response
    brain = OllamaBrain(host="http://127.0.0.1:99999", timeout=1)
    msg = Message(role=Role.USER, content="Hi")
    resp = brain.generate_response([msg])
    assert "[JARVIS Error:" in resp.text
