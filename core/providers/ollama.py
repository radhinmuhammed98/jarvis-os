"""
Local Ollama / OpenAI-compatible API Brain Provider
"""

import json
import logging
import urllib.request
import urllib.error
from typing import List, Generator, Optional, Dict, Any

from core.brain import BaseBrain
from core.types import Message, ResponseChunk, Role

logger = logging.getLogger("jarvis-ollama-provider")

class OllamaBrain(BaseBrain):
    """
    Connects to local Ollama API instance (default http://127.0.0.1:11434).
    Supports local execution with small models (e.g. llama3.2:1b, qwen2.5:3b, mistral, etc.).
    """

    def __init__(self, host: str = "http://127.0.0.1:11434", model: str = "llama3.2:1b", timeout: int = 30):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate_response(self, messages: List[Message], system_prompt: Optional[str] = None) -> ResponseChunk:
        payload = self._build_payload(messages, system_prompt, stream=False)
        url = f"{self.host}/api/chat"

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("message", {}).get("content", "")
                return ResponseChunk(text=content, is_final=True)
        except Exception as e:
            logger.error(f"Ollama API request failed: {e}")
            return ResponseChunk(text=f"[JARVIS Error: Unable to reach local model engine at {self.host} - {e}]", is_final=True)

    def stream_response(self, messages: List[Message], system_prompt: Optional[str] = None) -> Generator[ResponseChunk, None, None]:
        payload = self._build_payload(messages, system_prompt, stream=True)
        url = f"{self.host}/api/chat"

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                for line in resp:
                    if line:
                        chunk_data = json.loads(line.decode("utf-8"))
                        text_part = chunk_data.get("message", {}).get("content", "")
                        done = chunk_data.get("done", False)
                        yield ResponseChunk(text=text_part, is_final=done)
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            yield ResponseChunk(text=f"[JARVIS Error: Connection to local model failed: {e}]", is_final=True)

    def _build_payload(self, messages: List[Message], system_prompt: Optional[str], stream: bool) -> Dict[str, Any]:
        formatted_msgs = []
        if system_prompt:
            formatted_msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            formatted_msgs.append({"role": m.role.value, "content": m.content})

        return {
            "model": self.model,
            "messages": formatted_msgs,
            "stream": stream,
            "options": {"temperature": 0.3}
        }
