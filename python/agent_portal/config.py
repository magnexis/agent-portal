from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import RuntimeConfigModel


DEFAULT_CONFIG_PATH = "agent-portal.config.json"


def load_config(base_path: Path | None = None) -> RuntimeConfigModel:
    root = base_path or Path.cwd()
    config_path = root / DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return RuntimeConfigModel()

    raw = json.loads(config_path.read_text(encoding="utf8"))
    return RuntimeConfigModel(**raw)


def save_default_config(base_path: Path | None = None) -> Path:
    root = base_path or Path.cwd()
    config_path = root / DEFAULT_CONFIG_PATH
    if not config_path.exists():
        config_path.write_text(
            json.dumps(asdict(RuntimeConfigModel()), indent=2),
            encoding="utf8",
        )
    return config_path
