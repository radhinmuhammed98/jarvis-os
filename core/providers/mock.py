"""
Mock Brain Provider for local offline testing and CI/CD validation.
"""

from typing import List, Generator, Optional, Tuple
from core.brain import BaseBrain
from core.types import Message, ResponseChunk, Intent, IntentType, ActionProposal

class MockBrain(BaseBrain):
    """Deterministically simulates AI responses and action proposals without external dependencies."""

    def __init__(self, model_name: str = "mock-brain-v1"):
        self.model_name = model_name

    def generate_response(self, messages: List[Message], system_prompt: Optional[str] = None) -> ResponseChunk:
        last_msg = messages[-1].content if messages else ""
        return ResponseChunk(text=f"JARVIS [Mock]: Received '{last_msg}'", is_final=True)

    def stream_response(self, messages: List[Message], system_prompt: Optional[str] = None) -> Generator[ResponseChunk, None, None]:
        last_msg = messages[-1].content if messages else "Hello"
        words = f"JARVIS [Mock]: Processing query '{last_msg}'.".split()
        for i, word in enumerate(words):
            is_last = (i == len(words) - 1)
            yield ResponseChunk(text=word + (" " if not is_last else ""), is_final=is_last)

    def extract_intent_and_action(
        self, user_input: str, context: List[Message]
    ) -> Tuple[Intent, Optional[ActionProposal]]:
        lowered = user_input.lower()
        if "run" in lowered or "execute" in lowered or "list files" in lowered:
            intent = Intent(
                intent_type=IntentType.SYSTEM_COMMAND,
                confidence=0.95,
                summary="User requested file listing or command execution.",
                parameters={"raw": user_input}
            )
            action = ActionProposal(
                action_type="shell_execution",
                description="List directory contents",
                target="local_system",
                parameters={"command": "ls -la"},
                risk_level="low",
                requires_confirmation=True
            )
            return intent, action

        intent = Intent(
            intent_type=IntentType.CONVERSATION,
            confidence=0.99,
            summary="Standard conversational input",
            parameters={}
        )
        return intent, None
