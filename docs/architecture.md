# JARVIS OS Architecture Overview

## Overview
JARVIS OS is designed as an agentic operating system where the primary interface and process model center around local AI capabilities, voice interaction, and autonomous sandbox execution.

## Layer Breakdown

1. **Debian Base & Kernel**
   - Debian Bookworm minimal installation base.
   - Standard 64-bit Linux kernel (`linux-image-amd64`) with non-free firmware for Wi-Fi, Ethernet, CPU microcode, and GPU device support.

2. **System Layer (`system/`)**
   - Handles low-level OS bootstrap (`jarvis-init`).
   - Hardware detection (GPU, CPU, Memory, Audio devices, Network interfaces).
   - System health checks and telemetry.

3. **Audio & Network Foundations**
   - PipeWire / ALSA audio backend for low-latency microphone input and speaker output.
   - NetworkManager / systemd-networkd for automatic connectivity.

4. **JARVIS Voice & Boot Integration (`voice/`)**
   - Always-on background systemd service (`jarvis-voice.service`).
   - Replaceable wake-word detector interface (`BaseWakeWordDetector`).
   - Explicit state machine (`OFF` -> `INITIALIZING` -> `IDLE` -> `WAKE_DETECTED` -> `LISTENING` -> `PROCESSING` -> `SPEAKING` -> `INTERRUPTED`).
   - Microphone discovery, automatic device selection, and graceful offline fallback.
   - Streaming STT, TTS, listening timeout, follow-up conversation mode, and barge-in speech interruption.

5. **JARVIS Subsystems (Core, Agent, Sandbox, Memory, Tools)**
   - Modular Python-native services configured to start post-boot.
   - Strict Intent Engine + Validation Gate + Permission Policy security pipeline before tool execution.
   - Isolated sandbox layer for agent code execution.
