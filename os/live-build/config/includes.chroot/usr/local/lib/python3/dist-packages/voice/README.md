# JARVIS Voice Subsystem (`voice/`)

The **Voice Subsystem** provides an always-on, local-first streaming voice pipeline featuring wake-word detection, explicit state transitions, audio device initialization and recovery, Voice Activity Detection (VAD), Speech-To-Text (STT), Text-To-Speech (TTS), listening timeout management, follow-up conversation mode, and real-time barge-in speech interruption.

## Architecture & Boot Pipeline

```text
Boot -> systemd (jarvis-voice.service) -> Voice Service -> Wake Word Detector -> Voice Pipeline
  ↓
[IDLE State] -> Wake Phrase ("JARVIS") -> [LISTENING State] -> Streaming STT
  ↓
Finalized Utterance -> JARVIS Core -> Intent Engine -> Validation Gate -> Permission Policy -> Tools -> [SPEAKING State] -> TTS
                                                                                                            │
                                                                          [User Barge-In Interrupt] ◄───────┘
```

## Voice State Machine

The voice subsystem operates according to an explicit `VoiceStateMachine` with strict transition rules:

- `OFF`: Service uninitialized.
- `INITIALIZING`: Audio device discovery and hardware initialization.
- `IDLE`: Low-power background monitoring for wake-word detection.
- `WAKE_DETECTED`: Wake word triggered; transitioning to active listening.
- `LISTENING`: Active STT stream processing spoken input.
- `PROCESSING`: Finalized utterance being evaluated by Core, Intent Engine, and Validation Gate.
- `SPEAKING`: Output response stream active via TTS.
- `INTERRUPTED`: User barge-in detected during speech playback; halting TTS immediately and resuming listening.
- `ERROR`: Subsystem error; attempting hardware or state recovery back to `INITIALIZING` or `IDLE`.

## Key Guarantees & Security Rules

1. **Wake Word Is NOT an Action Trigger**: Detecting the wake phrase ("JARVIS") only activates the listening session and never executes system actions directly.
2. **Partial Transcriptions**: Partial STT results do NOT trigger action evaluation or computer command execution.
3. **Utterance Finalization**: Only complete finalized utterances pass through the Intent Engine, Validation Gate, Permission Policy, and Tool Registry.
4. **Barge-In Interruption**: User speech during TTS playback immediately halts speech output.
5. **Privacy & Offline First**: All wake-word processing, STT, and TTS run completely local without external cloud streaming or telemetry.
