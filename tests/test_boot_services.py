import os
import sys
import subprocess
import pytest

CHROOT_ROOT = "os/live-build/config/includes.chroot"
SYSTEMD_DIR = os.path.join(CHROOT_ROOT, "etc/systemd/system")
WANTS_DIR = os.path.join(SYSTEMD_DIR, "multi-user.target.wants")
TARGET_PACKAGES_DIR = os.path.join(CHROOT_ROOT, "usr/local/lib/python3/dist-packages")


def test_services_enabled_in_target_filesystem():
    assert os.path.isdir(WANTS_DIR), f"Directory {WANTS_DIR} does not exist"

    sys_link = os.path.join(WANTS_DIR, "jarvis-system.service")
    voice_link = os.path.join(WANTS_DIR, "jarvis-voice.service")

    assert os.path.exists(sys_link) or os.path.islink(sys_link), "jarvis-system.service is not enabled in multi-user.target.wants"
    assert os.path.exists(voice_link) or os.path.islink(voice_link), "jarvis-voice.service is not enabled in multi-user.target.wants"


def test_service_ordering_and_dependencies():
    sys_path = os.path.join(SYSTEMD_DIR, "jarvis-system.service")
    voice_path = os.path.join(SYSTEMD_DIR, "jarvis-voice.service")

    with open(sys_path, "r") as f:
        sys_content = f.read()

    with open(voice_path, "r") as f:
        voice_content = f.read()

    assert "After=multi-user.target" not in sys_content, "jarvis-system.service must not rely on After=multi-user.target"
    assert "After=multi-user.target" not in voice_content, "jarvis-voice.service must not rely on After=multi-user.target"

    assert "Requires=jarvis-system.service" in voice_content, "jarvis-voice.service must require jarvis-system.service"
    assert "After=" in voice_content and "jarvis-system.service" in voice_content, "jarvis-voice.service must be ordered After jarvis-system.service"


def test_required_executables_modules_users_and_configs():
    init_script = os.path.join(CHROOT_ROOT, "usr/local/bin/jarvis-init")
    assert os.path.isfile(init_script), f"{init_script} missing"
    assert os.access(init_script, os.X_OK), f"{init_script} is not executable"

    with open(init_script, "r") as f:
        init_content = f.read()
    assert "P_CMD" not in init_content, "Obfuscated P_CMD string found in jarvis-init"
    assert "python3 -m system.init" in init_content, "jarvis-init must launch python3 -m system.init"

    required_modules = ["agent", "core", "memory", "sandbox", "system", "tools", "voice"]
    for mod in required_modules:
        mod_dir = os.path.join(TARGET_PACKAGES_DIR, mod)
        assert os.path.isdir(mod_dir), f"Required Python module package {mod} missing in target filesystem at {mod_dir}"
        assert os.path.isfile(os.path.join(mod_dir, "__init__.py")), f"__init__.py missing in package {mod}"

    assert os.path.isfile(os.path.join(TARGET_PACKAGES_DIR, "system/init.py")), "system.init module missing"
    assert os.path.isfile(os.path.join(TARGET_PACKAGES_DIR, "voice/pipeline.py")), "voice.pipeline module missing"

    cfg_file = os.path.join(CHROOT_ROOT, "etc/jarvis/config.json")
    assert os.path.isfile(cfg_file), "/etc/jarvis/config.json missing in target filesystem"

    sysusers_file = os.path.join(CHROOT_ROOT, "etc/sysusers.d/jarvis.conf")
    assert os.path.isfile(sysusers_file), "/etc/sysusers.d/jarvis.conf missing"

    models_dir = os.path.join(CHROOT_ROOT, "var/lib/jarvis/models")
    logs_dir = os.path.join(CHROOT_ROOT, "var/log/jarvis")
    assert os.path.isdir(models_dir), f"Models directory {models_dir} missing in target filesystem"
    assert os.path.isdir(logs_dir), f"Logs directory {logs_dir} missing in target filesystem"

    hook_file = "os/live-build/config/hooks/live/0100-jarvis-setup.hook.chroot"
    assert os.path.isfile(hook_file), f"{hook_file} missing"
    assert os.access(hook_file, os.X_OK), f"{hook_file} is not executable"


def test_target_filesystem_python_imports():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(TARGET_PACKAGES_DIR)

    code = "import system.init; import voice.pipeline; import agent.intent_engine; import agent.validation_gate; import tools.registry; import tools.permissions; import sandbox.runtime; import system.computer; import core.service; print('IMPORT_SUCCESS')"

    res = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert res.returncode == 0, f"Failed to import modules from target filesystem: {res.stderr}"
    assert "IMPORT_SUCCESS" in res.stdout


def test_jarvis_init_execution_in_target_environment():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(TARGET_PACKAGES_DIR)

    init_script = os.path.abspath(os.path.join(CHROOT_ROOT, "usr/local/bin/jarvis-init"))
    res = subprocess.run([init_script], env=env, capture_output=True, text=True)

    assert res.returncode == 0, f"jarvis-init failed to execute: {res.stderr}\nOutput: {res.stdout}"
    assert "System Initialization Complete" in res.stdout or "JARVIS OS is ready" in res.stdout


def test_security_hardening_and_non_root():
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
    enabled_files = set(os.listdir(WANTS_DIR))
    allowed_services = {"jarvis-system.service", "jarvis-voice.service"}
    unrelated = enabled_files - allowed_services
    assert not unrelated, f"Unrelated services enabled in target filesystem: {unrelated}"


def test_build_iso_script_check():
    res = subprocess.run(["./os/build_iso.sh", "--check"], capture_output=True, text=True)
    assert res.returncode == 0, f"build_iso.sh --check failed: {res.stderr}\nOutput: {res.stdout}"
