#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LIVE_BUILD_DIR="${SCRIPT_DIR}/live-build"
BUILD_DIR="${SCRIPT_DIR}/build"

CHECK_ONLY=0
if [[ "${1:-}" == "--check" ]]; then
    CHECK_ONLY=1
fi

echo "===> JARVIS OS ISO Builder <==="

# Verification checks
echo "[1/4] Validating build configuration..."
if [[ ! -f "${LIVE_BUILD_DIR}/config/package-lists/jarvis.list.chroot" ]]; then
    echo "Error: Package list not found!"
    echo "FAILURE"
fi

# Check for forbidden Desktop Environment packages
FORBIDDEN_PKGS="gnome|kde|xfce|lxde|mate|cinnamon|x11-common|wayland|lightdm|gdm3|sddm"
if grep -E "^($FORBIDDEN_PKGS)" "${LIVE_BUILD_DIR}/config/package-lists/jarvis.list.chroot" >/dev/null 2>&1; then
    echo "Error: Desktop Environment package detected in package list!"
    echo "FAILURE"
fi

# Check live-build auto/config bootloader options
AUTO_CONFIG="${LIVE_BUILD_DIR}/auto/config"
if [[ -f "$AUTO_CONFIG" ]]; then
    if grep -q "grub-live" "$AUTO_CONFIG"; then
        echo "Error: Invalid bootloader 'grub-live' found in auto/config!"
        echo "FAILURE"
    fi
    if grep -q "debian-installer false" "$AUTO_CONFIG"; then
        echo "Error: Deprecated '--debian-installer false' found in auto/config! Use 'none'."
        echo "FAILURE"
    fi
fi

echo "[2/4] Package list and bootloader configuration validation passed."

if [[ "$CHECK_ONLY" -eq 1 ]]; then
    echo "=== Configuration check completed successfully. ==="
else
    if [[ $EUID -ne 0 ]]; then
        echo "Error: Building the ISO image requires root privileges. Please run with sudo."
    else
        echo "[3/4] Running live-build..."
        mkdir -p "$BUILD_DIR"
        cd "$LIVE_BUILD_DIR"
        lb clean --purge
        lb config
        lb build

        if ls *.iso >/dev/null 2>&1; then
            mv *.iso "${BUILD_DIR}/jarvis-os-minimal.iso"
            echo "[4/4] ISO build complete: ${BUILD_DIR}/jarvis-os-minimal.iso"
        else
            echo "Error: ISO generation failed."
        fi
    fi
fi
