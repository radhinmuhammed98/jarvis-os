"""
JARVIS OS System Layer Configuration & Initialization Logic
"""

import os
import sys
import json
import logging
from typing import Dict, Any

from system.health import HardwareDetector

DEFAULT_CONFIG_PATH = "/etc/jarvis/config.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [JARVIS-SYSTEM] %(message)s")
logger = logging.getLogger("jarvis-system")

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config at {config_path}: {e}")
    return {
        "system_name": "JARVIS OS",
        "version": "0.1.0-milestone1",
        "auto_boot": True,
        "subsystems": {
            "core": True,
            "voice": True,
            "agent": True,
            "sandbox": True,
            "memory": True,
            "tools": True
        }
    }

def initialize_system(check_only: bool = False) -> int:
    logger.info("Initializing JARVIS OS System Layer...")
    config = load_config()
    sys_name = config.get("system_name", "JARVIS OS")
    sys_ver = config.get("version", "0.1.0")
    logger.info(f"System: {sys_name} (v{sys_ver})")

    inventory = HardwareDetector.get_full_inventory()
    cores = inventory["cpu"]["cores"]
    mem = inventory["memory"]["total_mb"]
    logger.info(f"Hardware Inventory Detected: CPU Cores={cores}, Memory={mem}MB")
    if inventory["gpu"]["has_gpu"]:
        logger.info(f"GPU Detected: {inventory['gpu']['gpus']}")
    else:
        logger.info("No dedicated GPU detected via lspci.")

    enabled_subsystems = [sub for sub, enabled in config.get("subsystems", {}).items() if enabled]
    logger.info(f"Enabled Subsystems: {', '.join(enabled_subsystems)}")

    if check_only:
        logger.info("System layer check completed successfully.")
        return 0

    logger.info("JARVIS OS System Initialization Complete. Ready for agent operations.")
    return 0

if __name__ == "__main__":
    check_mode = "--check" in sys.argv
    sys.exit(initialize_system(check_only=check_mode))
