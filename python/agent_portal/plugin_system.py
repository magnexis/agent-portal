from __future__ import annotations

import json
from pathlib import Path

from .models import PluginManifestModel


PLUGIN_DIR = "plugins"


def discover_plugins(base_path: Path | None = None) -> list[Path]:
    root = base_path or Path.cwd()
    plugin_root = root / PLUGIN_DIR
    if not plugin_root.exists():
        return []
    return sorted(plugin_root.glob("*/plugin.json"))


def load_plugin_manifest(plugin_path: Path) -> PluginManifestModel:
    raw = json.loads(plugin_path.read_text(encoding="utf8"))
    return PluginManifestModel(**raw)


def validate_plugin_manifest(plugin_path: Path) -> list[str]:
    try:
        manifest = load_plugin_manifest(plugin_path)
    except Exception as exc:
        return [f"Failed to load manifest {plugin_path}: {exc}"]

    errors: list[str] = []
    if not manifest.name:
        errors.append("Plugin manifest is missing a name.")
    if not manifest.version:
        errors.append("Plugin manifest is missing a version.")
    if not manifest.type:
        errors.append("Plugin manifest is missing a type.")
    if not isinstance(manifest.permissions, list):
        errors.append("Plugin permissions must be a list.")
    if not isinstance(manifest.commands, list):
        errors.append("Plugin commands must be a list.")
    return errors
