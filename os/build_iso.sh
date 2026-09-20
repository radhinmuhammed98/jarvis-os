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
validation_errors=0

if [[ ! -f "${LIVE_BUILD_DIR}/config/package-lists/jarvis.list.chroot" ]]; then
    echo "Error: Package list not found!"
    validation_errors=1
fi

# Check for forbidden heavy Desktop Environment packages
FORBIDDEN_PKGS="gnome|kde|plasma|cinnamon|mate|lxde|gdm3|sddm"
if grep -E "^($FORBIDDEN_PKGS)" "${LIVE_BUILD_DIR}/config/package-lists/jarvis.list.chroot" >/dev/null 2>&1; then
    echo "Error: Forbidden heavy Desktop Environment package detected in package list!"
    validation_errors=1
fi

# Check live-build auto/config bootloader options
AUTO_CONFIG="${LIVE_BUILD_DIR}/auto/config"
if [[ -f "$AUTO_CONFIG" ]]; then
    if grep -q "grub-live" "$AUTO_CONFIG"; then
        echo "Error: Invalid bootloader 'grub-live' found in auto/config!"
        validation_errors=1
    fi
    if grep -q "debian-installer false" "$AUTO_CONFIG"; then
        echo "Error: Deprecated '--debian-installer false' found in auto/config! Use 'none'."
        validation_errors=1
    fi
fi

# Check boot-time JARVIS service integration
SYS_SVC="${LIVE_BUILD_DIR}/config/includes.chroot/etc/systemd/system/jarvis-system.service"
VOICE_SVC="${LIVE_BUILD_DIR}/config/includes.chroot/etc/systemd/system/jarvis-voice.service"
WANTS_DIR="${LIVE_BUILD_DIR}/config/includes.chroot/etc/systemd/system/multi-user.target.wants"

if [[ ! -f "$SYS_SVC" ]]; then
    echo "Error: jarvis-system.service missing!"
    validation_errors=1
fi

if [[ ! -f "$VOICE_SVC" ]]; then
    echo "Error: jarvis-voice.service missing!"
    validation_errors=1
fi

if [[ ! -e "${WANTS_DIR}/jarvis-system.service" ]]; then
    echo "Error: jarvis-system.service is not enabled in multi-user.target.wants!"
    validation_errors=1
fi

if [[ ! -e "${WANTS_DIR}/jarvis-voice.service" ]]; then
    echo "Error: jarvis-voice.service is not enabled in multi-user.target.wants!"
    validation_errors=1
fi

# Verify ordering & dependency rules
if grep -q "After=multi-user.target" "$SYS_SVC" "$VOICE_SVC"; then
    echo "Error: Invalid systemd ordering 'After=multi-user.target' detected in service files!"
    validation_errors=1
fi

if ! grep -q "Requires=jarvis-system.service" "$VOICE_SVC" || ! grep -q "After=.*jarvis-system.service" "$VOICE_SVC"; then
    echo "Error: jarvis-voice.service must require and be ordered after jarvis-system.service!"
    validation_errors=1
fi

# Security & User validation
if ! grep -q "User=jarvis" "$VOICE_SVC" || ! grep -q "Group=jarvis" "$VOICE_SVC"; then
    echo "Error: jarvis-voice.service must run under user and group 'jarvis'!"
    validation_errors=1
fi

for hardening in "NoNewPrivileges=true" "ProtectSystem=full" "ProtectHome=read-only" "PrivateTmp=true"; do
    if ! grep -q "$hardening" "$VOICE_SVC"; then
        echo "Error: jarvis-voice.service missing security hardening directive: $hardening"
        validation_errors=1
    fi
done

# Executable, config, and Python module checks
INIT_SCRIPT="${LIVE_BUILD_DIR}/config/includes.chroot/usr/local/bin/jarvis-init"
if [[ ! -x "$INIT_SCRIPT" ]]; then
    echo "Error: /usr/local/bin/jarvis-init missing or not executable!"
    validation_errors=1
fi

if grep -q "P_CMD" "$INIT_SCRIPT"; then
    echo "Error: Obfuscated string bug found in /usr/local/bin/jarvis-init!"
    validation_errors=1
fi

CFG_FILE="${LIVE_BUILD_DIR}/config/includes.chroot/etc/jarvis/config.json"
if [[ ! -f "$CFG_FILE" ]]; then
    echo "Error: /etc/jarvis/config.json missing!"
    validation_errors=1
fi

PY_PACKAGES_DIR="${LIVE_BUILD_DIR}/config/includes.chroot/usr/local/lib/python3/dist-packages"
REQUIRED_MODS=("agent" "core" "memory" "sandbox" "system" "tools" "voice")
for mod in "${REQUIRED_MODS[@]}"; do
    if [[ ! -d "${PY_PACKAGES_DIR}/${mod}" ]]; then
        echo "Error: Python package '${mod}' missing in target filesystem at ${PY_PACKAGES_DIR}/${mod}!"
        validation_errors=1
    fi
done

if [[ $validation_errors -ne 0 ]]; then
    echo "Error: Build configuration validation failed!"
    exit 1
fi

echo "[2/4] Package list, bootloader configuration, and JARVIS service integration validation passed."

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
