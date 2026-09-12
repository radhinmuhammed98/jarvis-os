# AGENTS.md - JARVIS OS Contributor & Agent Guidelines

Welcome to **JARVIS OS**. This repository houses the minimal, reproducible, voice-first Linux operating system designed specifically for running JARVIS agents and services natively on x86_64 hardware.

---

## 1. Architecture Principles

1. **Minimal & Headless**: JARVIS OS boots straight into the JARVIS system layer (`jarvis-init`) via systemd without any Desktop Environment (No GNOME, KDE, X11, or Wayland).
2. **Reproducible Builds**: Built using Debian `live-build`. All package configurations, system hooks, and image options must be completely declarative under `os/live-build/`.
3. **No AI Model Weights in Git**: Git contains system code, drivers, configuration tools, and agent logic. AI models are dynamically fetched and validated post-install by the JARVIS Model Manager.
4. **Modular Subsystems**:
   - `os/`: Live-build configs and ISO build scripts.
   - `core/`: Core event loops and system orchestration.
   - `voice/`: Audio pipeline (STT / TTS interfaces).
   - `agent/`: Agent logic and task execution.
   - `sandbox/`: Isolated execution environments.
   - `memory/`: Short and long-term state persistence.
   - `tools/`: Tool interfaces for agents.
   - `system/`: OS bootstrap, hardware detection, and health checks.
   - `tests/`: Automated test suite.
   - `docs/`: Architecture specifications and guides.

---

## 2. Coding & Contribution Rules

- **Python**: PEP 8 style, python 3.11+, typed annotations where practical.
- **Shell Scripts**: Portable POSIX/Bash scripts (`set -euo pipefail`), non-interactive debconf settings.
- **Testing**: All code in `system/` and build configurations under `os/` must be covered by automated tests in `tests/`.
- **Pre-commit Checks**: Run `pytest` before committing any changes.

---

## 3. Build & Test Commands

- **Run tests**:
  ```bash
  pytest
  ```
- **Dry-run live-build configuration check**:
  ```bash
  ./os/build_iso.sh --check
  ```
- **Build ISO image (requires root / sudo)**:
  ```bash
  sudo ./os/build_iso.sh
  ```
