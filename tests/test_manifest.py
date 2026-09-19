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


def test_live_build_auto_config_bootloader():
    config_path = "os/live-build/auto/config"
    assert os.path.isfile(config_path), "live-build auto/config script does not exist"

    with open(config_path, "r") as f:
        content = f.read()

    assert "grub-live" not in content, "Invalid bootloader 'grub-live' found in auto/config"
    assert "debian-installer false" not in content, "Deprecated '--debian-installer false' found in auto/config"
    assert "--bootloader syslinux" in content, "Expected '--bootloader syslinux' in auto/config"
    assert "--debian-installer none" in content, "Expected '--debian-installer none' in auto/config"
