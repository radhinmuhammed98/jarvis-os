"""
JARVIS Core Orchestrator Service
"""

import logging
from typing import Generator, Optional, Tuple, Dict, Any

from core.brain import BaseBrain
from core.providers.mock import MockBrain
from core.providers.ollama import OllamaBrain
from core.context import ConversationContext
from core.config import CoreConfig
from core.types import Role, Message, ResponseChunk, Intent, ActionProposal

logger = logging.getLogger("jarvis-core")

class JarvisCore:
    """
    JARVIS Core Orchestrator Process.
    Receives user input, manages context, communicates with the abstract Brain interface,
    and cleanly separates conversational output from proposed actions.
    NEVER executes action proposals directly.
    """

    def __init__(self, config: Optional[CoreConfig] = None):
        self.config = config or CoreConfig.load()
        self.brain: BaseBrain = self._init_brain()
        self.context = ConversationContext(
            max_messages=self.config.max_history,
            system_instruction=self.config.system_prompt
        )
        logger.info(f"Initialized JARVIS Core with provider '{self.config.provider}' using model '{self.config.model_name}'")

    def _init_brain(self) -> BaseBrain:
        prov = self.config.provider.lower()
        if prov == "ollama":
            return OllamaBrain(host=self.config.host, model=self.config.model_name)
        elif prov == "mock":
            return MockBrain(model_name=self.config.model_name)
        else:
            logger.warning(f"Unknown provider '{prov}', falling back to MockBrain.")
            return MockBrain(model_name="mock-fallback")

    def process_message(self, user_text: str) -> Dict[str, Any]:
        """
        Process user message synchronously.
        Returns dict containing response text, Intent, and Optional[ActionProposal].
        """
        self.context.add_message(Role.USER, user_text)
        messages = self.context.get_messages()

        # Step 1: Extract intent & action proposal without executing anything
        intent, action_proposal = self.brain.extract_intent_and_action(user_text, messages)

        # Step 2: Generate conversation response
        chunk = self.brain.generate_response(messages, system_prompt=self.config.system_prompt)

        # Save assistant response to history
        self.context.add_message(Role.ASSISTANT, chunk.text)

        return {
            "text": chunk.text,
            "intent": intent,
            "action_proposal": action_proposal,
            "executed": False  # Explicitly guarantee no auto-execution
        }

    def process_message_stream(self, user_text: str) -> Generator[ResponseChunk, None, None]:
        """
        Stream conversational response tokens to caller in real-time.
        Emits final chunk containing intent and optional action proposal.
        NEVER executes any actions.
        """
        self.context.add_message(Role.USER, user_text)
        messages = self.context.get_messages()

        intent, action_proposal = self.brain.extract_intent_and_action(user_text, messages)

        accumulated_text = []
        for chunk in self.brain.stream_response(messages, system_prompt=self.config.system_prompt):
            accumulated_text.append(chunk.text)
            if chunk.is_final:
                final_text = "".join(accumulated_text)
                self.context.add_message(Role.ASSISTANT, final_text)
                yield ResponseChunk(
                    text=chunk.text,
                    is_final=True,
                    intent=intent,
                    action_proposal=action_proposal
                )
            else:
                yield chunk
