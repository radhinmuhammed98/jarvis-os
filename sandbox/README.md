# JARVIS Sandbox Subsystem (`sandbox/`)

The **Sandbox** subsystem provides secure, isolated execution for untrusted, generated, or user-supplied code.

## Threat Model & Security Boundaries

1. **Host Secret Isolation**: The sandbox environment strips all host API keys, SSH credentials, environment secrets, and sensitive paths.
2. **Resource Limits**: Enforces POSIX resource limits (`RLIMIT_CPU`, `RLIMIT_AS` memory limits, `RLIMIT_NPROC` process limits) and strict timeout thresholds.
3. **Filesystem Isolation**: Subprocesses run inside clean, isolated temporary workspace directories (`/tmp/jarvis_sb_*`) that are automatically destroyed upon completion.
4. **Network Deny-by-Default**: Disables outward network egress by routing through invalid proxy endpoints unless explicitly permitted.
5. **Permission Gate Requirement**: Code execution MUST pass through the Permission Policy engine (`sandbox:execute`).

## Known Escape Risks & Future Mitigation

- *Kernel Exploits*: Subprocess isolation relies on kernel namespace and resource limits. Full OS containers (Bubblewrap / Docker / Firecracker) can be integrated as secondary backend providers in future milestones.
