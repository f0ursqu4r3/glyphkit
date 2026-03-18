"""Platform registry for iconforge."""

from __future__ import annotations

import pathlib
from typing import Callable

from PIL import Image

PlatformGenerator = Callable[[Image.Image, pathlib.Path, dict], list[pathlib.Path]]

from iconforge.platforms.ios import generate as ios_generate
from iconforge.platforms.android import generate as android_generate
from iconforge.platforms.macos import generate as macos_generate
from iconforge.platforms.windows import generate as windows_generate
from iconforge.platforms.web import generate as web_generate
from iconforge.platforms.linux import generate as linux_generate

PLATFORM_REGISTRY: dict[str, PlatformGenerator] = {
    "ios": ios_generate,
    "android": android_generate,
    "macos": macos_generate,
    "windows": windows_generate,
    "web": web_generate,
    "linux": linux_generate,
}

VALID_PLATFORMS = list(PLATFORM_REGISTRY.keys())
