"""Dependency detection and install assistance."""

import platform
import shutil
import subprocess


def check_dependency(name: str) -> bool:
    """Check if a binary is available on PATH."""
    return shutil.which(name) is not None


def get_install_command(name: str, brew: str = None, apt: str = None) -> str:
    """Return platform-specific install command string."""
    system = platform.system()
    if system == "Darwin" and brew:
        return f"brew install {brew}"
    elif system == "Linux" and apt:
        return f"sudo apt-get install -y {apt}"
    else:
        return f"Install {name} manually: https://git-scm.com/downloads"


def try_install(name: str, brew: str = None, apt: str = None) -> bool:
    """Attempt to install a dependency. Returns True if successful."""
    if check_dependency(name):
        return True
    system = platform.system()
    try:
        if system == "Darwin" and brew and shutil.which("brew"):
            subprocess.run(
                ["brew", "install", brew],
                check=True, capture_output=True, text=True,
            )
            return check_dependency(name)
        elif system == "Linux" and apt:
            subprocess.run(
                ["sudo", "apt-get", "install", "-y", apt],
                check=True, capture_output=True, text=True,
            )
            return check_dependency(name)
    except (subprocess.CalledProcessError, OSError):
        pass
    return False
