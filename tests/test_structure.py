import os
import pytest

REQUIRED_DIRS = [
    "os/live-build",
    "core",
    "voice",
    "agent",
    "sandbox",
    "memory",
    "tools",
    "system",
    "tests",
    "docs"
]

def test_directory_structure():
    for d in REQUIRED_DIRS:
        assert os.path.isdir(d), f"Missing required directory: {d}"

def test_essential_files():
    assert os.path.isfile("AGENTS.md"), "Missing AGENTS.md"
    assert os.path.isfile("README.md"), "Missing README.md"
    assert os.path.isfile("os/build_iso.sh"), "Missing os/build_iso.sh"
    assert os.path.isfile("os/live-build/config/package-lists/jarvis.list.chroot"), "Missing package list"
