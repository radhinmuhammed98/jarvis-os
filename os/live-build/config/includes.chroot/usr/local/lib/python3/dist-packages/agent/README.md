# JARVIS Agent Subsystem (`agent/`)

The **Agent** subsystem contains the Intent Engine and Validation Gate for JARVIS OS.

## Architecture Pipeline

```text
User Utterance + Context
          │
          ▼
     Intent Engine
          │
          ├── Classification: conversation | question | information_request | action_request | ambiguous | cancel
          └── Reference Resolution: ("it", "that" -> "Chrome")
          │
          ▼
    Action Proposal
          │
          ▼
   Validation Gate (Policy & Safety Checks)
          │
          ▼
Candidate Proposal (Awaiting Permission / Sandbox Approval - NOT Executed)
```

## Security Directive
The Intent Engine and Validation Gate **NEVER** execute system tools directly.
