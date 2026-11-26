"""
Ollama Service Manager.
Automatically detects if the local Ollama server is running and boots 'ollama serve'
in the background if it is not currently active.
"""

import os
import sys
import shutil
import time
import logging
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

logger = logging.getLogger("Ori.Ollama")


def find_ollama_binary() -> Path | None:
    """Locate the ollama executable across Windows, Linux (Pi), and macOS."""
    # 1. Check system PATH
    which_path = shutil.which("ollama")
    if which_path:
        return Path(which_path)

    # 2. Check Windows standard LocalAppData install location
    if sys.platform == "win32":
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        if local_appdata:
            win_path = Path(local_appdata) / "Programs" / "Ollama" / "ollama.exe"
            if win_path.exists():
                return win_path

    # 3. Check Linux / Raspberry Pi standard locations
    for p in [Path("/usr/local/bin/ollama"), Path("/usr/bin/ollama"), Path.home() / ".ollama" / "bin" / "ollama"]:
        if p.exists():
            return p

    return None


def is_ollama_running(url: str = "http://127.0.0.1:11434") -> bool:
    """Ping Ollama HTTP endpoint to check if it's currently responding."""
    try:
        req = urllib.request.Request(url.rstrip("/"), method="HEAD")
        with urllib.request.urlopen(req, timeout=1.5):
            return True
    except (urllib.error.URLError, ConnectionError, OSError):
        return False
    except Exception:
        return False


def ensure_ollama_running(url: str = "http://127.0.0.1:11434", max_wait_seconds: int = 10) -> bool:
    """
    Checks if Ollama is running; if not, automatically launches 'ollama serve'
    as an independent background daemon process.
    """
    if is_ollama_running(url):
        logger.info("🦙 Ollama server is already running and responsive.")
        return True

    logger.warning("🦙 Ollama server is not running. Attempting to start 'ollama serve' automatically...")

    ollama_bin = find_ollama_binary()
    if not ollama_bin:
        logger.error("❌ Could not locate the 'ollama' executable on this system. Please ensure Ollama is installed.")
        return False

    logger.info(f"🚀 Launching Ollama daemon: {ollama_bin} serve")

    # Set process flags to run cleanly in background without popping windows on Windows
    kwargs = {}
    if sys.platform == "win32":
        # CREATE_NO_WINDOW = 0x08000000
        kwargs["creationflags"] = 0x08000000

    try:
        subprocess.Popen(
            [str(ollama_bin), "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            **kwargs
        )
    except Exception as e:
        logger.error(f"❌ Failed to launch 'ollama serve': {e}")
        return False

    # Poll endpoint until ready
    start_time = time.time()
    while time.time() - start_time < max_wait_seconds:
        time.sleep(1.0)
        if is_ollama_running(url):
            logger.info("✨ Ollama server started successfully and is now ready for inference!")
            return True

    logger.warning("⚠️ Started 'ollama serve' process, but endpoint has not responded yet. Continuing anyway...")
    return False
