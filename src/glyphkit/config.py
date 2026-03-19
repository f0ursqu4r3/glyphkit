"""Config file support for glyphkit."""

from __future__ import annotations

import pathlib

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

CONFIG_FILENAME = ".glyphkit.toml"


def load_config(directory: pathlib.Path | None = None) -> dict:
    """Load config from .glyphkit.toml if it exists. Returns empty dict if not found."""
    if directory is None:
        directory = pathlib.Path.cwd()
    config_path = directory / CONFIG_FILENAME
    if not config_path.exists():
        return {}
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def get_option(config: dict, key: str, cli_value, default):
    """Get option value: CLI flag overrides config, which overrides default.

    For CLI flags, argparse defaults need special handling — we only use
    the CLI value if it was explicitly provided (not the argparse default).
    """
    # Config value takes precedence over default
    config_value = config.get(key, default)
    # CLI value takes precedence over config (if not the argparse default)
    if cli_value != default:
        return cli_value
    return config_value
