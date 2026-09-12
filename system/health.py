"""
JARVIS OS Hardware Detection & System Telemetry Module
"""

import os
import sys
import json
import subprocess
import platform
from typing import Dict, Any

class HardwareDetector:
    """Detects CPU, Memory, GPU, Audio, and Networking hardware."""

    @staticmethod
    def detect_cpu() -> Dict[str, Any]:
        info = {
            "arch": platform.machine(),
            "processor": platform.processor(),
            "cores": os.cpu_count() or 1,
        }
        return info

    @staticmethod
    def detect_memory() -> Dict[str, Any]:
        total_mb = 0
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        parts = line.split()
                        total_mb = int(parts[1]) // 1024
                        break
        except Exception:
            total_mb = 0
        return {"total_mb": total_mb}

    @staticmethod
    def detect_gpu() -> Dict[str, Any]:
        gpus = []
        try:
            res = subprocess.run(["lspci"], capture_output=True, text=True, check=False)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "VGA" in line or "3D" in line or "Display" in line:
                        gpus.append(line.strip())
        except FileNotFoundError:
            gpus.append("lspci not available")
        return {"gpus": gpus, "has_gpu": len(gpus) > 0}

    @staticmethod
    def detect_audio() -> Dict[str, Any]:
        audio_devices = []
        try:
            res = subprocess.run(["lspci"], capture_output=True, text=True, check=False)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "Audio" in line or "Sound" in line:
                        audio_devices.append(line.strip())
        except FileNotFoundError:
            audio_devices.append("lspci not available")
        return {"audio_devices": audio_devices}

    @staticmethod
    def get_full_inventory() -> Dict[str, Any]:
        return {
            "cpu": HardwareDetector.detect_cpu(),
            "memory": HardwareDetector.detect_memory(),
            "gpu": HardwareDetector.detect_gpu(),
            "audio": HardwareDetector.detect_audio(),
            "os": platform.system(),
            "release": platform.release(),
        }
