"""Platform registry for iconforge."""

from __future__ import annotations

from iconforge.platforms.ios import generate as ios_generate
from iconforge.platforms.android import generate as android_generate

PLATFORM_REGISTRY: dict[str, object] = {
    "ios": ios_generate,
    "android": android_generate,
}
