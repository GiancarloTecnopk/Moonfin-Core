#!/usr/bin/env python3
"""Apply approved Moonfin REC artwork to build outputs (Android TV/Windows).

This is intentionally CI-only: stock Moonfin icons outside the REC build remain
unchanged.  Rebuild native launcher resources from the checked-in approved PNG.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/branding/moonfin_rec_icon_256.png"
EXPECTED_SHA256 = "59479cc426012f9e562b4ca8fb6a7762d4779f1e3ce7e916f9337cd89dd8c9de"


def font(size: int):
    for path in (
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def banner_from(icon: Image.Image) -> Image.Image:
    # Standard Android TV application banner (320 x 180).
    banner = Image.new("RGB", (320, 180), "#031123")
    d = ImageDraw.Draw(banner)
    # Understated blue gradient, unlike a blurred/app-generated screenshot.
    for y in range(180):
        d.line([(0, y), (319, y)], fill=(2, 13 + y // 16, 29 + y // 12))
    square = icon.resize((152, 152), Image.Resampling.LANCZOS).convert("RGB")
    banner.paste(square, (10, 14))
    d.text((172, 55), "Moonfin", font=font(22), fill="#E8F7FF")
    d.text((174, 93), "REC", font=font(34), fill="#FF414B")
    d.rounded_rectangle((173, 137, 277, 140), radius=2, fill="#E52636")
    return banner


def apply_android(icon: Image.Image) -> None:
    base = ROOT / "android/app/src/androidTv/res/drawable-nodpi"
    base.mkdir(parents=True, exist_ok=True)
    # Android can't package a .jpg and .png with the same resource name.
    legacy = base / "moonfin_rec_launcher.jpg"
    if legacy.exists():
        legacy.unlink()
    launcher = base / "moonfin_rec_launcher.png"
    icon.save(launcher, format="PNG", optimize=True)
    banner = ROOT / "android/app/src/main/res/drawable-nodpi/moonfin_tv_banner.png"
    banner.parent.mkdir(parents=True, exist_ok=True)
    banner_from(icon).save(banner, format="PNG", optimize=True)
    manifest = (ROOT / "android/app/src/androidTv/AndroidManifest.xml").read_text()
    if 'android:icon="@drawable/moonfin_rec_launcher"' not in manifest:
        raise RuntimeError("Android TV manifest is not using REC launcher icon")
    print(f"Android TV: {launcher} and {banner}")


def apply_windows(icon: Image.Image) -> None:
    ico = ROOT / "windows/runner/resources/app_icon.ico"
    ico.parent.mkdir(parents=True, exist_ok=True)
    icon.convert("RGBA").save(
        ico,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
               (64, 64), (128, 128), (256, 256)],
    )
    runner = (ROOT / "windows/runner/Runner.rc").read_text(encoding="utf-8")
    if "app_icon.ico" not in runner:
        raise RuntimeError("Windows resource file does not reference app_icon.ico")
    print(f"Windows executable + Inno Setup: {ico} ({ico.stat().st_size} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--android", action="store_true")
    parser.add_argument("--windows", action="store_true")
    args = parser.parse_args()
    if not args.android and not args.windows:
        parser.error("Specify --android and/or --windows")

    data = SOURCE.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != EXPECTED_SHA256:
        raise RuntimeError(f"Approved Moonfin REC icon hash mismatch: {actual}")
    with Image.open(SOURCE) as loaded:
        if loaded.size != (256, 256):
            raise RuntimeError(f"Unexpected icon size: {loaded.size}")
        icon = loaded.convert("RGB")
    if args.android:
        apply_android(icon)
    if args.windows:
        apply_windows(icon)


if __name__ == "__main__":
    main()
