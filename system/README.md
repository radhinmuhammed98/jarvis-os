# JARVIS OS - SYSTEM Subsystem
This directory contains components for the JARVIS OS system layer.
# JARVIS Computer Control Subsystem (`system/computer.py` & `tools/computer.py`)

The **Computer Control** subsystem provides platform abstractions for application lifecycle, window management, and audio control.

## Architecture & Security Boundaries

```text
User Input -> Intent Engine -> Validation Gate -> Permission Policy -> Tool Registry -> Computer Control Tool -> Host / Mock Backend
```

### Allowlist Application Model
Application launch/close operations map exclusively to a validated dictionary of allowlisted application keys (`chrome`, `firefox`, `spotify`, `terminal`, `vscode`, `vlc`). Arbitrary paths or raw shell command strings are strictly rejected.
