"""
JARVIS Intent Engine
Classifies user utterances and resolves context references (e.g. "it", "that", "the first one").
"""

import re
from typing import List, Optional, Tuple, Dict, Any
from core.types import Message, Intent, IntentCategory, ActionProposal, Role

class IntentEngine:
    """
    Analyzes complete user utterances in combination with conversation context.
    Determines intent category and constructs candidate ActionProposals if intent is action_request.
    Enforces that keywords alone do NOT trigger action proposals.
    """

    ACTION_VERBS = {
        "open": "app_launch",
        "launch": "app_launch",
        "start": "app_launch",
        "run": "shell_execution",
        "close": "app_close",
        "stop": "app_close",
        "kill": "app_close",
        "terminate": "app_close",
        "delete": "file_delete",
        "remove": "file_delete"
    }

    CANCEL_PHRASES = ["cancel", "don't", "dont", "nevermind", "stop", "abort", "actually don't", "actually, don't"]

    def analyze(self, user_text: str, context: List[Message]) -> Tuple[Intent, Optional[ActionProposal]]:
        text_clean = user_text.strip()
        lowered = text_clean.lower()

        # Clean trailing punctuation for word checks
        clean_words = [w.strip(".,!?") for w in lowered.split()]

        # 1. Check for cancellation
        for cancel_phrase in self.CANCEL_PHRASES:
            if cancel_phrase in lowered:
                intent = Intent(
                    category=IntentCategory.CANCEL,
                    confidence=0.98,
                    summary="User explicitly cancelled previous operation.",
                    parameters={}
                )
                return intent, None

        # 2. Check for question intent ("do you know...", "what is...", "how do I...", "?")
        if text_clean.endswith("?") or lowered.startswith("do you know") or lowered.startswith("what is") or lowered.startswith("how do"):
            intent = Intent(
                category=IntentCategory.QUESTION,
                confidence=0.95,
                summary="User asked a question.",
                parameters={"query": text_clean}
            )
            return intent, None

        # 3. Check for conversational statement mentioning applications without imperative command verb
        # e.g., "Chrome is really slow today.", "Chrome... hmm, maybe I'll use Firefox."
        if ("..." in lowered or "maybe" in lowered or "think" in lowered or "is" in lowered) and not (clean_words and clean_words[0] in self.ACTION_VERBS):
            if "maybe" in lowered or "..." in lowered:
                intent = Intent(
                    category=IntentCategory.AMBIGUOUS,
                    confidence=0.85,
                    summary="Ambiguous user thought or statement.",
                    parameters={}
                )
            else:
                intent = Intent(
                    category=IntentCategory.INFORMATION_REQUEST,
                    confidence=0.90,
                    summary="User made an informational observation.",
                    parameters={}
                )
            return intent, None

        # 4. Check for imperative command verb at start
        action_verb = None
        target_raw = ""

        if clean_words and clean_words[0] in self.ACTION_VERBS:
            action_verb = clean_words[0]
            target_raw = " ".join([w.strip(".,!?") for w in lowered.split()[1:]]).strip()

        if not action_verb:
            # Not an imperative action request
            intent = Intent(
                category=IntentCategory.CONVERSATION,
                confidence=0.90,
                summary="Standard conversation input.",
                parameters={}
            )
            return intent, None

        # 5. Resolve target references (pronouns: "it", "that", "this", "the app")
        resolved_target = self._resolve_target(target_raw, context)

        if not resolved_target:
            # Cannot resolve target -> Ambiguous / Needs clarification
            intent = Intent(
                category=IntentCategory.AMBIGUOUS,
                confidence=0.5,
                summary=f"Action '{action_verb}' requested, but target '{target_raw}' is ambiguous or unresolvable.",
                requires_clarification=True,
                clarification_prompt=f"What would you like me to {action_verb}?"
            )
            return intent, None

        # 6. Valid Action Request with resolved target
        action_type = self.ACTION_VERBS[action_verb]
        intent = Intent(
            category=IntentCategory.ACTION_REQUEST,
            confidence=0.95,
            summary=f"User requested to {action_verb} {resolved_target}.",
            parameters={"verb": action_verb, "target": resolved_target}
        )

        proposal = ActionProposal(
            action_type=action_type,
            description=f"{action_verb.capitalize()} {resolved_target}",
            target=resolved_target,
            parameters={"target": resolved_target, "command_verb": action_verb},
            confidence=0.95,
            risk_level="low" if action_type in ["app_launch", "app_close"] else "medium",
            requires_confirmation=True
        )

        return intent, proposal

    def _resolve_target(self, target_raw: str, context: List[Message]) -> Optional[str]:
        target_clean = re.sub(r'^(the|a|an)\s+', '', target_raw.strip(), flags=re.IGNORECASE)

        # If target is explicit and not a pronoun
        PRONOUNS = ["it", "that", "this", "the first one", "one", ""]
        if target_clean and target_clean not in PRONOUNS:
            return target_clean

        # Target is a pronoun or empty -> Search context backward for mentioned target entities
        for msg in reversed(context):
            content = msg.content
            # Search for common application names or entities in previous messages
            matches = re.findall(r'\b(Chrome|Firefox|Spotify|Terminal|VSCode|VLC)\b', content, re.IGNORECASE)
            if matches:
                return matches[-1]

        return None
