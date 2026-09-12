# Live-Build Pipeline Specifications

## Live-Build Configuration (`os/live-build/`)

The live-build tree is structured as follows:

```text
os/live-build/
├── auto/
│   ├── config    # Sets lb config flags (distribution, archive-areas, binary images)
│   ├── build     # Runs lb build
│   └── clean     # Cleans build artifacts
└── config/
    ├── package-lists/
    │   └── jarvis.list.chroot   # Manifest of required system packages
    └── includes.chroot/
        ├── etc/
        │   ├── jarvis/config.json
        │   └── systemd/system/jarvis-system.service
        └── usr/local/bin/jarvis-init
```

## Package Manifest Principles
- **Included**: `linux-image-amd64`, `firmware-linux`, `pipewire`, `alsa-utils`, `network-manager`, `python3`, `systemd`.
- **Excluded**: X11, Wayland, GNOME, KDE, XFCE, LightDM, GDM, SDDM, or any desktop applications.
