"""
Configuration Management for JARVIS Core
"""

import os
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional

DEFAULT_CONFIG_PATH = "/etc/jarvis/config.json"

@dataclass
class CoreConfig:
    provider: str = "mock"  # "mock", "ollama", "llamacpp"
    model_name: str = "mock-brain-v1"
    host: str = "http://127.0.0.1:11434"
    max_history: int = 20
    system_prompt: str = "You are JARVIS OS, a helpful, local, secure operating system assistant."

    @classmethod
    def load(cls, config_file: Optional[str] = None) -> "CoreConfig":
        file_path = config_file or os.getenv("JARVIS_CONFIG_PATH", DEFAULT_CONFIG_PATH)
        data: Dict[str, Any] = {}

        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f).get("core", {})
            except Exception:
                pass

        return cls(
            provider=os.getenv("JARVIS_BRAIN_PROVIDER", data.get("provider", "mock")),
            model_name=os.getenv("JARVIS_MODEL_NAME", data.get("model_name", "mock-brain-v1")),
            host=os.getenv("JARVIS_MODEL_HOST", data.get("host", "http://127.0.0.1:11434")),
            max_history=int(os.getenv("JARVIS_MAX_HISTORY", data.get("max_history", 20))),
            system_prompt=data.get("system_prompt", "You are JARVIS OS, a helpful, local, secure operating system assistant.")
        )
