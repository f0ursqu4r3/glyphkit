"""Tests for config file loading."""

from __future__ import annotations

import pathlib

from glyphkit.config import load_config, get_option


class TestLoadConfig:
    def test_returns_empty_when_no_file(self, tmp_path: pathlib.Path) -> None:
        assert load_config(tmp_path) == {}

    def test_loads_toml_file(self, tmp_path: pathlib.Path) -> None:
        config_file = tmp_path / ".glyphkit.toml"
        config_file.write_text('platforms = ["ios", "web"]\npadding = 10\n')
        config = load_config(tmp_path)
        assert config["platforms"] == ["ios", "web"]
        assert config["padding"] == 10


class TestGetOption:
    def test_cli_overrides_config(self) -> None:
        config = {"padding": 10}
        assert get_option(config, "padding", 20, 0) == 20

    def test_config_overrides_default(self) -> None:
        config = {"padding": 10}
        assert get_option(config, "padding", 0, 0) == 10

    def test_default_when_neither(self) -> None:
        assert get_option({}, "padding", 0, 0) == 0
