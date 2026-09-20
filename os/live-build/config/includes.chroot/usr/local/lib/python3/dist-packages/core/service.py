"""
JARVIS Core Orchestrator Service
Integrates IntentEngine and ValidationGate
"""

import logging
from typing import Generator, Optional, Tuple, Dict, Any

from core.brain import BaseBrain
from core.providers.mock import MockBrain
from core.providers.ollama import OllamaBrain
from core.context import ConversationContext
from core.config import CoreConfig
from core.types import Role, Message, ResponseChunk, Intent, IntentCategory, ActionProposal
from agent.intent_engine import IntentEngine
from agent.validation_gate import ValidationGate

logger = logging.getLogger("jarvis-core")

class JarvisCore:
    """
    JARVIS Core Orchestrator Process.
    Receives user input, manages context, uses IntentEngine & ValidationGate,
    and communicates with the abstract Brain interface.
    NEVER executes action proposals directly.
    """

    def __init__(self, config: Optional[CoreConfig] = None):
        self.config = config or CoreConfig.load()
        self.brain: BaseBrain = self._init_brain()
        self.intent_engine = IntentEngine()
        self.validation_gate = ValidationGate()
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
        Process user message synchronously through IntentEngine and ValidationGate.
        Returns dict containing response text, Intent, and Optional[ActionProposal].
        """
        messages = self.context.get_messages()

        # Step 1: Analyze intent and resolve context
        intent, action_proposal = self.intent_engine.analyze(user_text, messages)

        # Step 2: Pass through ValidationGate if proposal generated
        validated_proposal = None
        if action_proposal:
            valid, reason, validated_proposal = self.validation_gate.validate(intent, action_proposal)

        # Step 3: Handle clarification prompts or conversational responses
        if intent.requires_clarification and intent.clarification_prompt:
            reply_text = intent.clarification_prompt
        elif intent.category == IntentCategory.CANCEL:
            reply_text = "Understood. Action cancelled."
        else:
            self.context.add_message(Role.USER, user_text)
            chunk = self.brain.generate_response(self.context.get_messages(), system_prompt=self.config.system_prompt)
            reply_text = chunk.text
            self.context.add_message(Role.ASSISTANT, reply_text)

        return {
            "text": reply_text,
            "intent": intent,
            "action_proposal": validated_proposal or action_proposal,
            "executed": False  # Explicit guarantee: 0 action execution
        }

    def process_message_stream(self, user_text: str) -> Generator[ResponseChunk, None, None]:
        """
        Stream conversational response tokens to caller in real-time.
        Passes through IntentEngine and ValidationGate.
        NEVER executes any actions.
        """
        messages = self.context.get_messages()

        intent, action_proposal = self.intent_engine.analyze(user_text, messages)

        validated_proposal = None
        if action_proposal:
            valid, reason, validated_proposal = self.validation_gate.validate(intent, action_proposal)

        if intent.requires_clarification and intent.clarification_prompt:
            yield ResponseChunk(
                text=intent.clarification_prompt,
                is_final=True,
                intent=intent,
                action_proposal=None
            )
            return

        if intent.category == IntentCategory.CANCEL:
            yield ResponseChunk(
                text="Understood. Action cancelled.",
                is_final=True,
                intent=intent,
                action_proposal=None
            )
            return

        self.context.add_message(Role.USER, user_text)
        accumulated_text = []

        for chunk in self.brain.stream_response(self.context.get_messages(), system_prompt=self.config.system_prompt):
            accumulated_text.append(chunk.text)
            if chunk.is_final:
                final_text = "".join(accumulated_text)
                self.context.add_message(Role.ASSISTANT, final_text)
                yield ResponseChunk(
                    text=chunk.text,
                    is_final=True,
                    intent=intent,
                    action_proposal=validated_proposal or action_proposal
                )
            else:
                yield chunk
