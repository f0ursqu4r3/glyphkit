"""CLI entrypoint for glyphkit."""

from __future__ import annotations

import argparse
import pathlib
import sys

from glyphkit.core import GlyphkitError, load_and_validate_image
from glyphkit.platforms import PLATFORM_REGISTRY, VALID_PLATFORMS


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="glyphkit",
        description="Universal app icon generator",
    )
    parser.add_argument("--source", help="Path to source image (PNG, JPEG, WebP, or SVG)")
    parser.add_argument(
        "--platforms", help="Comma-separated platforms: " + ", ".join(VALID_PLATFORMS)
    )
    parser.add_argument(
        "--output-dir", default="./glyphkit-output", help="Output directory"
    )
    parser.add_argument(
        "--android-bg", default="#FFFFFF", help="Android adaptive icon background color"
    )
    parser.add_argument("--padding", type=int, default=0, help="Padding percentage (0-50)")
    parser.add_argument("--bg-color", default="", help="Background fill color (hex, e.g. #FFFFFF)")
    parser.add_argument(
        "--no-prompt", action="store_true", help="Skip interactive prompts"
    )
    parser.add_argument("--ui", action="store_true", help="Launch web UI")
    return parser.parse_args(argv)


def run(
    source: pathlib.Path,
    platforms: list[str],
    output_dir: pathlib.Path,
    options: dict,
) -> None:
    """Validate inputs and dispatch to platform generators."""
    # Validate platforms
    invalid = [p for p in platforms if p not in PLATFORM_REGISTRY]
    if invalid:
        raise GlyphkitError(
            f"Invalid platform(s): {', '.join(invalid)}. "
            f"Valid platforms: {', '.join(VALID_PLATFORMS)}"
        )

    from glyphkit.core import apply_background, apply_padding

    img = load_and_validate_image(source)

    padding = options.get("padding", 0)
    if padding:
        img = apply_padding(img, padding)

    bg_color = options.get("bg_color", "")
    if bg_color:
        img = apply_background(img, bg_color)

    for platform_name in platforms:
        print(f"Generating {platform_name} icons...")
        platform_dir = output_dir / platform_name
        generator = PLATFORM_REGISTRY[platform_name]
        files = generator(img, platform_dir, options)
        print(f"  {platform_name}: {len(files)} files created")


def _interactive_prompts() -> tuple[pathlib.Path, list[str], dict]:
    """Run interactive questionary prompts."""
    import questionary

    platforms = questionary.checkbox(
        "Select target platforms:",
        choices=VALID_PLATFORMS,
    ).ask()
    if not platforms:
        print("No platforms selected.")
        sys.exit(0)

    source_str = questionary.path("Source image path:").ask()
    if not source_str:
        print("No source image provided.")
        sys.exit(1)

    options: dict = {"padding": 0, "bg_color": ""}
    if "android" in platforms:
        bg = questionary.text(
            "Android background color (hex):",
            default="#FFFFFF",
        ).ask()
        options["android_bg"] = bg or "#FFFFFF"

    return pathlib.Path(source_str), platforms, options


def main() -> None:
    """Main entrypoint."""
    args = parse_args()

    if args.ui:
        try:
            from glyphkit.web.server import start_server
        except ImportError:
            print(
                "Error: Web UI requires extra dependencies. "
                "Install with: uv pip install -e '.[ui]'",
                file=sys.stderr,
            )
            sys.exit(1)
        start_server()
        return

    if args.no_prompt:
        if not args.source or not args.platforms:
            print(
                "Error: --source and --platforms required with --no-prompt",
                file=sys.stderr,
            )
            sys.exit(1)
        source = pathlib.Path(args.source)
        platforms = [p.strip() for p in args.platforms.split(",")]
        options = {"android_bg": args.android_bg, "padding": args.padding, "bg_color": args.bg_color}
    else:
        source, platforms, options = _interactive_prompts()

    output_dir = pathlib.Path(args.output_dir)
    try:
        run(source=source, platforms=platforms, output_dir=output_dir, options=options)
    except GlyphkitError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print("Done!")


if __name__ == "__main__":
    main()
