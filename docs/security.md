# JARVIS OS Security Model & Permission Architecture

## Core Security Guarantees

1. **Model Isolation**
   - The LLM inference engine operates purely as a text-and-intent generator.
   - The model output cannot directly trigger executable binaries, system calls, or shell commands.

2. **ActionProposal Pipeline & Validation Gate**
   - All proposed actions must be encapsulated in structured `ActionProposal` objects.
   - The `ValidationGate` verifies ambiguity, confidence thresholds, and safety policies.

3. **Tool Registry & Permission System**
   - **Default DENY**: Unknown tool IDs or unpermitted actions are rejected immediately.
   - Tools explicitly declare input schemas and required permission strings (e.g. `system:read`, `time:read`).
   - Parameters are validated against tool input schemas prior to invocation.

4. **Auditability**
   - All proposal phases (`PROPOSED`, `APPROVED`, `REJECTED`, `DRY_RUN`, `EXECUTED`) are recorded in structured audit logs.
