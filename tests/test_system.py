import pytest
from system.health import HardwareDetector
from system.init import load_config, initialize_system

def test_hardware_detector():
    inventory = HardwareDetector.get_full_inventory()
    assert "cpu" in inventory
    assert "memory" in inventory
    assert "gpu" in inventory
    assert "audio" in inventory
    assert inventory["cpu"]["cores"] >= 1

def test_load_config():
    config = load_config("non_existent_config.json")
    assert config["system_name"] == "JARVIS OS"
    assert config["auto_boot"] is True

def test_initialize_system_check():
    res = initialize_system(check_only=True)
    assert res == 0
