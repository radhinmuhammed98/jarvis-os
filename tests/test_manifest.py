import os

FORBIDDEN_DESKTOP_PACKAGES = [
    "gnome", "kde", "xfce", "lxde", "mate", "cinnamon", "x11-common",
    "wayland", "lightdm", "gdm3", "sddm"
]

REQUIRED_PACKAGES = [
    "linux-image-amd64",
    "firmware-linux",
    "pipewire",
    "alsa-utils",
    "network-manager",
    "systemd",
    "python3"
]

def test_manifest_packages():
    manifest_path = "os/live-build/config/package-lists/jarvis.list.chroot"
    assert os.path.isfile(manifest_path), "Manifest file does not exist"

    with open(manifest_path, "r") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    for forbidden in FORBIDDEN_DESKTOP_PACKAGES:
        assert forbidden not in lines, f"Forbidden Desktop Environment package '{forbidden}' found in manifest"

    for req in REQUIRED_PACKAGES:
        assert req in lines, f"Required package '{req}' missing from manifest"
