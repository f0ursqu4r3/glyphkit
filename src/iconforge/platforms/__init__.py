"""Platform registry for iconforge."""

from __future__ import annotations

from iconforge.platforms.ios import generate as ios_generate

PLATFORM_REGISTRY: dict[str, object] = {
    "ios": ios_generate,
}
