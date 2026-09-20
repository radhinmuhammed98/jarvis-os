"""
JARVIS Core Local Interactive CLI Interface
"""

import sys
import logging
from core.service import JarvisCore
from core.config import CoreConfig

def main():
    logging.basicConfig(level=logging.WARNING)
    config = CoreConfig.load()
    core = JarvisCore(config)

    print("=================================================================")
    print("                     JARVIS OS - Core CLI                        ")
    print(f" Provider: {config.provider} | Model: {config.model_name}")
    print(" Type 'exit' or 'quit' to stop.")
    print("=================================================================\n")

    while True:
        try:
            user_input = input("User > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("JARVIS OS shutting down session.")
                break

            print("JARVIS > ", end="", flush=True)
            action_prop = None
            intent_res = None

            for chunk in core.process_message_stream(user_input):
                print(chunk.text, end="", flush=True)
                if chunk.is_final:
                    action_prop = chunk.action_proposal
                    intent_res = chunk.intent

            print("\n")
            if intent_res:
                print(f"  [Intent Classified]: {intent_res.intent_type.value} (Confidence: {intent_res.confidence})")
            if action_prop:
                print(f"  [PROPOSED ACTION - NOT EXECUTED]:")
                print(f"    Type: {action_prop.action_type}")
                print(f"    Target: {action_prop.target}")
                print(f"    Params: {action_prop.parameters}")
                print(f"    Risk Level: {action_prop.risk_level}")
                print("    (Action execution deferred to Intent Validator / Agent layer)\n")

        except (KeyboardInterrupt, EOFError):
            print("\nJARVIS OS session terminated.")
            break

if __name__ == "__main__":
    main()
