"""
Milestone 03 Test Suite: Intent Engine, Validation Gate, and Action Isolation
Verify all required test cases and guarantee 0 tool execution occurs.
"""

import pytest
from core.service import JarvisCore
from core.config import CoreConfig
from core.types import IntentCategory

@pytest.fixture
def core():
    return JarvisCore(CoreConfig(provider="mock"))

def test_case_open_chrome(core):
    """'Open Chrome.' -> action proposal generated and validated."""
    res = core.process_message("Open Chrome.")
    assert res["intent"].category == IntentCategory.ACTION_REQUEST
    assert res["action_proposal"] is not None
    assert res["action_proposal"].target.lower() == "chrome"
    assert res["action_proposal"].action_type == "app_launch"
    assert res["action_proposal"].validated is True
    assert res["executed"] is False

def test_case_chrome_slow_today(core):
    """'Chrome is really slow today.' -> conversation/information, NO action proposal."""
    res = core.process_message("Chrome is really slow today.")
    assert res["intent"].category in [IntentCategory.INFORMATION_REQUEST, IntentCategory.CONVERSATION]
    assert res["action_proposal"] is None
    assert res["executed"] is False

def test_case_do_you_know_chrome(core):
    """'Do you know what Chrome is?' -> question, NO action proposal."""
    res = core.process_message("Do you know what Chrome is?")
    assert res["intent"].category == IntentCategory.QUESTION
    assert res["action_proposal"] is None
    assert res["executed"] is False

def test_case_chrome_maybe_firefox(core):
    """'Chrome... hmm, maybe I'll use Firefox.' -> ambiguous/conversation, NO action proposal."""
    res = core.process_message("Chrome... hmm, maybe I'll use Firefox.")
    assert res["intent"].category in [IntentCategory.AMBIGUOUS, IntentCategory.CONVERSATION]
    assert res["action_proposal"] is None
    assert res["executed"] is False

def test_case_close_spotify(core):
    """'Close Spotify.' -> action proposal generated."""
    res = core.process_message("Close Spotify.")
    assert res["intent"].category == IntentCategory.ACTION_REQUEST
    assert res["action_proposal"] is not None
    assert res["action_proposal"].target.lower() == "spotify"
    assert res["action_proposal"].action_type == "app_close"
    assert res["executed"] is False

def test_case_open_it_no_target(core):
    """'Open it.' with no resolvable target -> clarification required."""
    res = core.process_message("Open it.")
    assert res["intent"].requires_clarification is True
    assert "What would you like me to open?" in res["text"]
    assert res["action_proposal"] is None
    assert res["executed"] is False

def test_case_open_it_after_discussing_chrome(core):
    """'Open it.' after discussing Chrome -> action proposal targeting Chrome."""
    # First mention Chrome in conversation context
    core.process_message("Do you know what Chrome is?")
    # Follow up with "Open it."
    res = core.process_message("Open it.")
    assert res["intent"].category == IntentCategory.ACTION_REQUEST
    assert res["action_proposal"] is not None
    assert res["action_proposal"].target.lower() == "chrome"
    assert res["executed"] is False

def test_case_actually_dont(core):
    """'Actually, don't.' -> cancellation."""
    res = core.process_message("Actually, don't.")
    assert res["intent"].category == IntentCategory.CANCEL
    assert "cancelled" in res["text"].lower()
    assert res["action_proposal"] is None
    assert res["executed"] is False

def test_guarantee_no_tool_execution(core):
    """Verify that across all operations executed is explicitly False."""
    utterances = [
        "Open Chrome.",
        "Chrome is really slow today.",
        "Close Spotify.",
        "Delete /etc/passwd"
    ]
    for u in utterances:
        res = core.process_message(u)
        assert res["executed"] is False, f"Violation: Tool execution detected for '{u}'!"
