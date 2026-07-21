import os
import tomllib
from pathlib import Path

# Determine config directory and settings path
config_dir = Path(__file__).resolve().parent
toml_path = config_dir / "settings.toml"

# Default values
llm_provider = "ollama"
llm_model = "qwen2.5:7b-instruct"
llm_embed = "nomic-embed-text"

# Parse settings.toml if it exists
if toml_path.exists():
    try:
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
            llm_provider = data.get("llm_provider", llm_provider)
            llm_model = data.get("llm_model", llm_model)
            llm_embed = data.get("llm_embed", llm_embed)
    except Exception:
        pass
