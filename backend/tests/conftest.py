"""Pytest configuration for loading environment variables."""

import os
from pathlib import Path

env_file = Path(__file__).parent.parent / ".env"

if env_file.exists():
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key, value)
