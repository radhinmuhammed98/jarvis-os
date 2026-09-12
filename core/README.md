# JARVIS Core Subsystem (`core/`)

JARVIS Core is the local-first orchestrator service for **JARVIS OS**. It serves as the primary reasoning and conversation engine while enforcing a strict boundary between user conversation and action execution.

---

## Core Architecture & Pipeline

```text
User Input / Voice STT
          │
          ▼
    JARVIS CORE
          │
   ┌──────┴───────────────┐
   ▼                      ▼
Conversation Output   Action Proposal
   │                      │ (NOT Executed)
   ▼                      ▼
  TTS             Intent Validator / Agent
                          │
                          ▼
                       Sandbox
```

---

## Key Components

1. **`core/brain.py` (`BaseBrain`)**:
   - Abstract interface defining model generation, streaming responses, and intent extraction.
   - Decouples JARVIS Core from specific model providers or local backends.

2. **`core/providers/`**:
   - `MockBrain`: Offline deterministic provider for local development, CI/CD, and testing.
   - `OllamaBrain`: Client for local Ollama server (`http://127.0.0.1:11434`), optimized for local low-latency models on consumer GPUs (e.g., RTX 3050 4GB).

3. **`core/types.py`**:
   - Data structures for `Message`, `Intent`, `ActionProposal`, and `ResponseChunk`.
   - `ActionProposal` objects represent candidate actions that **must never be executed directly** by the model output.

4. **`core/service.py` (`JarvisCore`)**:
   - Persistent service that maintains conversation history (`core/context.py`) and orchestrates LLM queries.

5. **`core/cli.py`**:
   - Interactive CLI for testing text interactions with JARVIS Core.

---

## Running Local Interactive CLI

To run JARVIS Core interactively using the Mock provider:

```bash
JARVIS_BRAIN_PROVIDER=mock python3 -m core.cli
```

To run with a local Ollama model (e.g., `llama3.2:1b` or `qwen2.5:3b`):

1. Install and start Ollama locally:
   ```bash
   curl -fsSL https://ollama.com/install.sh | bash
   ollama serve
   ```
2. Pull a small compatible model suitable for 4GB VRAM:
   ```bash
   ollama pull llama3.2:1b
   ```
3. Run JARVIS Core CLI:
   ```bash
   JARVIS_BRAIN_PROVIDER=ollama JARVIS_MODEL_NAME=llama3.2:1b python3 -m core.cli
   ```
