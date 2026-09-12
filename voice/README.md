# JARVIS Voice Subsystem (`voice/`)

The **Voice Subsystem** provides streaming local-first audio capture, Voice Activity Detection (VAD), Speech-To-Text (STT), Text-To-Speech (TTS), and barge-in speech interruption.

## Architecture Pipeline

```text
Microphone Capture -> VAD -> Streaming STT -> Finalized Utterance -> JARVIS Core -> Intent Engine -> Validation Gate -> Tool Exec / TTS Output
                                                                                                                       │
                                                                                     [User Barge-In Interrupt] ◄───────┘
```

## Guarantees

1. **Partial Transcriptions**: Partial speech results do NOT trigger action evaluation or computer execution.
2. **Utterance Finalization**: Only complete finalized utterances are dispatched to the Intent Engine and Validation Gate.
3. **Barge-In Interruption**: If the user speaks while JARVIS is speaking via TTS, TTS playback is interrupted immediately.
