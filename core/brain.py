"""
Brain Abstraction Interface for Local AI Inference Engines
"""

from abc import ABC, abstractmethod
from typing import List, Generator, Optional, Dict, Any
from core.types import Message, ResponseChunk, Intent, ActionProposal

class BaseBrain(ABC):
    """
    Abstract Brain interface.
    Allows swapping local LLM inference engines (Ollama, llama.cpp, vLLM, Mock, etc.)
    without modifying the JARVIS Core orchestrator or agent system.
    """

    @abstractmethod
    def generate_response(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None
    ) -> ResponseChunk:
        """Generate a complete response synchronously."""
        pass

    @abstractmethod
    def stream_response(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None
    ) -> Generator[ResponseChunk, None, None]:
        """Stream response chunks in real-time."""
        pass

    @abstractmethod
    def extract_intent_and_action(
        self,
        user_input: str,
        context: List[Message]
    ) -> tuple[Intent, Optional[ActionProposal]]:
        """
        Analyze user input to classify Intent and propose ActionProposal if applicable.
        NOTE: Never executes the action.
        """
        pass
