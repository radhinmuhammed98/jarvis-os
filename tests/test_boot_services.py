import os
import subprocess
import pytest

CHROOT_ROOT = "os/live-build/config/includes.chroot"
SYSTEMD_DIR = os.path.join(CHROOT_ROOT, "etc/systemd/system")
WANTS_DIR = os.path.join(SYSTEMD_DIR, "multi-user.target.wants")


def test_services_enabled_in_target_filesystem():
    """Requirement 1, 2, 12: Prove both jarvis services are enabled in multi-user.target.wants."""
    assert os.path.isdir(WANTS_DIR), f"Directory {WANTS_DIR} does not exist"

    sys_link = os.path.join(WANTS_DIR, "jarvis-system.service")
    voice_link = os.path.join(WANTS_DIR, "jarvis-voice.service")

    assert os.path.exists(sys_link) or os.path.islink(sys_link), "jarvis-system.service is not enabled in multi-user.target.wants"
    assert os.path.exists(voice_link) or os.path.islink(voice_link), "jarvis-voice.service is not enabled in multi-user.target.wants"


def test_service_ordering_and_dependencies():
    """Requirement 3, 4, 8, 12: Prove jarvis-system is ordered before jarvis-voice and no After=multi-user.target exists."""
    sys_path = os.path.join(SYSTEMD_DIR, "jarvis-system.service")
    voice_path = os.path.join(SYSTEMD_DIR, "jarvis-voice.service")

    with open(sys_path, "r") as f:
        sys_content = f.read()

    with open(voice_path, "r") as f:
        voice_content = f.read()

    # Neither service should rely on After=multi-user.target
    assert "After=multi-user.target" not in sys_content, "jarvis-system.service must not rely on After=multi-user.target"
    assert "After=multi-user.target" not in voice_content, "jarvis-voice.service must not rely on After=multi-user.target"

    # Dependency: jarvis-system -> jarvis-voice
    assert "Requires=jarvis-system.service" in voice_content, "jarvis-voice.service must require jarvis-system.service"
    assert "After=" in voice_content and "jarvis-system.service" in voice_content, "jarvis-voice.service must be ordered After jarvis-system.service"


def test_required_executables_modules_users_and_configs():
    """Requirement 5, 6, 7, 12: Prove executable, python module, user/group config, and config.json exist."""
    init_script = os.path.join(CHROOT_ROOT, "usr/local/bin/jarvis-init")
    assert os.path.isfile(init_script), f"{init_script} missing"
    assert os.access(init_script, os.X_OK), f"{init_script} is not executable"

    # Check python voice module
    voice_pkg = os.path.join(CHROOT_ROOT, "usr/local/lib/python3/dist-packages/voice")
    assert os.path.isdir(voice_pkg), "Python voice package missing in target filesystem"
    assert os.path.isfile(os.path.join(voice_pkg, "pipeline.py")), "voice.pipeline missing"

    # Check config.json
    cfg_file = os.path.join(CHROOT_ROOT, "etc/jarvis/config.json")
    assert os.path.isfile(cfg_file), "/etc/jarvis/config.json missing in target filesystem"

    # Check sysusers configuration for jarvis user/group
    sysusers_file = os.path.join(CHROOT_ROOT, "etc/sysusers.d/jarvis.conf")
    assert os.path.isfile(sysusers_file), "/etc/sysusers.d/jarvis.conf missing"

    # Check chroot setup hook
    hook_file = "os/live-build/config/hooks/live/0100-jarvis-setup.hook.chroot"
    assert os.path.isfile(hook_file), f"{hook_file} missing"
    assert os.access(hook_file, os.X_OK), f"{hook_file} is not executable"


def test_security_hardening_and_non_root():
    """Requirement 10, 11: Prove security hardening flags and non-root execution."""
    voice_path = os.path.join(SYSTEMD_DIR, "jarvis-voice.service")
    with open(voice_path, "r") as f:
        voice_content = f.read()

    assert "User=jarvis" in voice_content, "jarvis-voice.service must run as User=jarvis"
    assert "Group=jarvis" in voice_content, "jarvis-voice.service must run as Group=jarvis"
    assert "NoNewPrivileges=true" in voice_content
    assert "ProtectSystem=full" in voice_content
    assert "ProtectHome=read-only" in voice_content
    assert "PrivateTmp=true" in voice_content


def test_no_unrelated_services_enabled():
    """Requirement 12: Prove no unrelated custom services are enabled in multi-user.target.wants."""
    enabled_files = set(os.listdir(WANTS_DIR))
    allowed_services = {"jarvis-system.service", "jarvis-voice.service"}
    unrelated = enabled_files - allowed_services
    assert not unrelated, f"Unrelated services enabled in target filesystem: {unrelated}"


def test_build_iso_script_check():
    """Requirement 14: Prove os/build_iso.sh --check passes."""
    res = subprocess.run(["./os/build_iso.sh", "--check"], capture_output=True, text=True)
    assert res.returncode == 0, f"build_iso.sh --check failed: {res.stderr}\nOutput: {res.stdout}"
