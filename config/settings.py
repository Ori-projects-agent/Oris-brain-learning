"""
Settings and configuration loader for the Autonomous Companion.
Loads persona specifications, environment variables, and runtime flags.
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
PERSONA_PATH = CONFIG_DIR / "persona.json"


def load_env_file(filepath: Path = BASE_DIR / ".env"):
    """Lightweight .env parser without external dependencies."""
    if not filepath.exists():
        return
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


# Load environment variables
load_env_file()


@dataclass
class Settings:
    # LLM Settings
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama")  # "ollama" or "gemini"
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    ollama_api_key: str = os.getenv("OLLAMA_API_KEY", "")

    # Local "two-brain" routing (100% local / Ollama):
    #   ollama_model      -> small fast model for routine heartbeat ticks
    #   ollama_deep_model -> bigger model for replying to your letters & nightly reflection
    #                        (falls back to ollama_model automatically if not downloaded)
    ollama_deep_model: str = os.getenv("OLLAMA_DEEP_MODEL", "") or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    # One shared context size for every call. Keeping it constant avoids Ollama reloading
    # the model between calls and lets it reuse the cached (unchanging) start of the prompt.
    ollama_num_ctx: int = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
    ollama_keep_alive: str = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
    ollama_timeout_seconds: int = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "300"))
    # Max tools offered to the model per tick (only the ones relevant to the current situation)
    max_tools_per_tick: int = int(os.getenv("MAX_TOOLS_PER_TICK", "8"))

    # Modeling Workshop (Blender + coding model)
    ollama_code_model: str = os.getenv("OLLAMA_CODE_MODEL", "qwen2.5-coder:14b")
    blender_path: str = os.getenv("BLENDER_PATH", r"C:\Users\nbbos\Projects\blender-4.5.15-windows-x64")

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Simulation & Tick Loop
    tick_interval_seconds: int = int(os.getenv("TICK_INTERVAL_SECONDS", "90"))
    db_path: str = os.getenv("DB_PATH", str(BASE_DIR / "ori_memory.db"))

    # Web & API Server
    web_host: str = os.getenv("WEB_HOST", "0.0.0.0")
    web_port: int = int(os.getenv("WEB_PORT", "8888"))

    # GitHub Integration
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_owner: str = os.getenv("GITHUB_OWNER", "")
    github_repo: str = os.getenv("GITHUB_REPO", "astral-archive")
    github_relics_path: str = os.getenv("GITHUB_RELICS_PATH", "data/custom_relic_library.json")

    # Astral Archive study game (learning curator integration).
    # Same PC: http://localhost:8080  |  Another machine on your network: http://<its-ip>:8080 (or :3000 on the Pi)
    astral_archive_url: str = os.getenv("ASTRAL_ARCHIVE_URL", "http://localhost:8080")

    # Archival Curator Reference 3D Model Source (optional external folder or .zip path)
    relic_reference_archive_dir: str = os.getenv("RELIC_REFERENCE_ARCHIVE_DIR", "")

    # Archival Curator Library Failsafes (anti-overflow caps)
    max_relic_library_size: int = int(os.getenv("MAX_RELIC_LIBRARY_SIZE", "255"))
    max_autonomous_relics_per_day: int = int(os.getenv("MAX_AUTONOMOUS_RELICS_PER_DAY", "3"))

    # Persona Data
    persona: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Settings":
        settings = cls()
        if PERSONA_PATH.exists():
            with open(PERSONA_PATH, "r", encoding="utf-8") as f:
                settings.persona = json.load(f)
        return settings


settings = Settings.load()
