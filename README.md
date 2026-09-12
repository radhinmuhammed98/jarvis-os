# JARVIS OS 🤖⚡

**JARVIS OS** is a minimal, reproducible, voice-first Linux operating system tailored for autonomous AI agents and local inference workloads.

---

## 🧱 Milestone 01 — Reproducible Debian Foundation

Milestone 01 establishes a headless, reproducible Debian live system configured to automatically boot directly into the JARVIS system startup sequence without any unnecessary desktop environments.

### Architecture Stack

```text
Debian Minimal (Bookworm / Testing)
    ↓
Linux Kernel + Firmware / Drivers
    ↓
Audio (PipeWire / ALSA) + Networking (NetworkManager / systemd-networkd)
    ↓
JARVIS System Layer (`jarvis-init`)
    ↓
Auto-boot into JARVIS
```

### Directory Structure

```text
jarvis-os/
├── os/
│   └── live-build/       # Debian live-build configs & package manifests
├── core/                 # Orchestrator & core event loops
├── voice/                # Audio pipeline & speech processing
├── agent/                # Autonomous agent logic
├── sandbox/              # Isolated runtime execution
├── memory/               # State & knowledge persistence
├── tools/                # Agent tools & integration
├── system/               # Hardware detection, system init & health checks
├── tests/                # Automated pytest suite
├── docs/                 # System documentation & architecture specs
├── AGENTS.md             # Contributor guidelines
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

Building the bootable ISO requires a Debian/Ubuntu host with `live-build` and `debootstrap` installed:

```bash
sudo apt-get update
sudo apt-get install -y live-build debootstrap xorriso isolinux syslinux-utils
```

### Validating Build Configuration

Run the configuration check without starting a full image build:

```bash
./os/build_iso.sh --check
```

### Building the ISO Image

To build the bootable ISO image:

```bash
sudo ./os/build_iso.sh
```

The output ISO will be saved to `os/build/jarvis-os-minimal.iso`.

### Testing System Layer Locally

You can test the JARVIS OS system layer init script directly using Python:

```bash
python3 -m system.init --check
```

Or run the test suite:

```bash
pytest
```

---

## 🛡️ Principles

1. **Headless & Minimal**: No desktop environment (X11/Wayland/GNOME).
2. **Reproducible**: Fully declarative package lists and system configurations.
3. **Clean Version Control**: No binary model weights in Git repositories. Model management happens dynamically post-installation.
