# JARVIS Tool Subsystem (`tools/`)

The **Tools** subsystem provides a secure, declarative, extensible framework for registering, validating, and executing tools in JARVIS OS.

## Security & Permission Model

1. **Default DENY**: Unregistered tools, disabled tools, or unpermitted requests are rejected immediately.
2. **No Arbitrary Code Execution**: The LLM model interface generates `ActionProposal` objects and CANNOT select or execute arbitrary binary/shell code.
3. **Schema Validation**: All input parameters are validated against JSON schema definitions before tool invocation.
4. **Permission Policy Engine**: Execution requires explicit permission grants (e.g. `system:read`, `time:read`, `echo:write`).
5. **Audit Logging**: Every operation emits structured audit records (`PROPOSED`, `APPROVED`, `REJECTED`, `DRY_RUN`, `EXECUTED`).
6. **Dry-Run Mode**: Allows testing proposal resolution without executing underlying logic.

## Initial Safe Demonstration Tools

- `system_info`: Returns basic OS and platform details.
- `time`: Returns system time and ISO string.
- `echo`: Returns supplied message string.
