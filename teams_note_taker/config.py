"""Configuration management - load/save settings from a config file."""

import json
import os

DEFAULT_CONFIG = {
    "whisper_model": "base",
    "language": None,
    "use_loopback": True,
    "device_id": None,
    "output_dir": "output",
    "output_format": "markdown",
    "meeting_title": None,
}

CONFIG_PATH = os.path.expanduser("~/.teams_note_taker.json")


def load_config():
    """Load configuration from file, falling back to defaults."""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            saved = json.load(f)
        config.update(saved)
    return config


def save_config(config):
    """Save configuration to file."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
