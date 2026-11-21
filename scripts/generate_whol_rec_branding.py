#!/usr/bin/env python3
"""Reproducible Wholphin REC launcher icon and Fire TV banner assets.

No external images or remote URLs: all Android densities are generated from
the same original vector-like fin + red REC art. This keeps launcher and
banner consistent across Fire OS and Android TV.
"""
from __future__ import annotations

import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
RES = ROOT / "app/src/main/res"
NAVY = (3, 16, 39, 255)
CYAN = (0, 202, 255, 255)
RED = (233, 23, 41, 255)
WHITE = (248, 252, 255, 255)


def font(size: int, bold: bool = True):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size)


def bezier(p0, p1, p2, p3, steps=72):
    out = []
    for k in range(steps + 1):
        t = k / steps
        s = 1 - t
        out.append((
            round(s**3 * p0[0] + 3*s*s*t*p1[0] + 3*s*t*t*p2[0] + t**3*p3[0]),
            round(s**3 * p0[1] + 3*s*s*t*p1[1] + 3*s*t*t*p2[1] + t**3*p3[1]),
        ))
    return out


def make_icon(n=512):
    im = Image.new("RGBA", (n, n), NAVY)
    d = ImageDraw.Draw(im)
    for y in range(n):
        dy = y / n
        d.line([(0, y), (n, y)], fill=(2, round(16+12*(1-dy)), round(39+26*(1-dy)), 255))
    border = Image.new("RGBA", (n, n), (0,0,0,0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((14, 14, n-14, n-14), radius=93, outline=(0,180,255,170), width=7)
    glow = border.filter(ImageFilter.GaussianBlur(12))
    im = Image.alpha_composite(im, glow)
    im = Image.alpha_composite(im, border)
    d = ImageDraw.Draw(im)
    # Fin silhouette and crest; design deliberately distinct from the
    # upstream Wholphin launcher while keeping familiar blue/white branding.
    main = (bezier((80,245),(174,202),(281,67),(407,82)) +
            bezier((407,82),(355,137),(328,201),(365,249)) +
            bezier((365,249),(285,214),(166,288),(80,245)))
    d.polygon(main, fill=(1, 146, 239, 255))
    highlight = (bezier((102,243),(215,175),(310,84),(405,84)) +
                 bezier((405,84),(315,103),(220,205),(102,243)))
    d.polygon(highlight, fill=(63, 237, 255, 248))
    wave = (bezier((57,245),(169,300),(261,188),(412,260)) +
            bezier((412,260),(285,224),(191,325),(57,245)))
    d.polygon(wave, fill=(0, 213, 247, 255))
    d.line(bezier((60,244),(178,297),(262,215),(420,260)), fill=(192,255,255,255), width=5, joint="curve")
    title = "Wholphin"
    title_font = font(64)
    box = d.textbbox((0,0), title, font=title_font)
    d.text(((n-(box[2]-box[0]))/2, 290), title, font=title_font, fill=WHITE, stroke_width=1, stroke_fill=(3,17,36))
    d.rounded_rectangle((126, 386, 391, 468), radius=24, fill=(191,11,28,255), outline=(255,62,73,255), width=3)
    d.ellipse((144,408,181,445), fill=(255,53,62,255), outline=(255,221,224,255), width=3)
    d.text((198,391), "REC", font=font(63), fill=WHITE)
    return im


def make_banner(icon: Image.Image):
    w,h=640,360
    im=Image.new("RGBA",(w,h),NAVY)
    d=ImageDraw.Draw(im)
    for y in range(h):
        d.line(((0,y),(w,y)),fill=(2, 13+int(10*y/h), 37+int(9*y/h),255))
    # Distinctive cyan and red framing for Android TV / Fire TV banner
    d.rounded_rectangle((7,7,w-8,h-8),radius=36,outline=(0,177,255,255),width=5)
    d.arc((42,-30,355,307),190,350, fill=(7,147,239,200),width=15)
    fin=icon.crop((24,45,476,290)).resize((278,151),Image.Resampling.LANCZOS)
    im.alpha_composite(fin,(20,82))
    d=ImageDraw.Draw(im)
    d.text((300,102),"Wholphin",font=font(40),fill=WHITE)
    d.rounded_rectangle((300,171,474,229),radius=16,fill=RED)
    d.ellipse((312,189,333,210),fill=WHITE)
    d.text((345,173),"REC",font=font(39),fill=WHITE)
    d.text((302,248),"LIVE TV  ·  DVR",font=font(18,False),fill=(155,220,245,255))
    return im


def put(path: Path, im: Image.Image, *, format: str, **params):
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, format=format, **params)
    print("brand:", path.relative_to(ROOT))


icon=make_icon()
banner=make_banner(icon)
densities={"mdpi":48, "hdpi":72, "xhdpi":96, "xxhdpi":144, "xxxhdpi":192}
for density,size in densities.items():
    folder=RES / f"mipmap-{density}"
    small=icon.resize((size,size),Image.Resampling.LANCZOS)
    # Match upstream file names/extension to avoid resource priority surprises.
    put(folder/"ic_launcher.webp", small, format="WEBP", quality=94)
    put(folder/"ic_launcher_round.webp", small, format="WEBP", quality=94)
    fore=Image.new("RGBA",(size,size),(0,0,0,0))
    art=icon.resize((int(size*.83),int(size*.83)),Image.Resampling.LANCZOS)
    fore.alpha_composite(art,((size-art.width)//2,(size-art.height)//2))
    put(folder/"ic_launcher_foreground.webp", fore, format="WEBP", quality=94)
    if density == "xhdpi":
        put(folder/"ic_banner.png", banner.resize((320,180),Image.Resampling.LANCZOS),format="PNG",optimize=True)
        put(folder/"ic_banner_foreground.png", banner.resize((320,180),Image.Resampling.LANCZOS),format="PNG",optimize=True)

# Fire TV uses the adaptive banner XML on API >= 26.
xml=RES/"mipmap-anydpi-v26/ic_banner.xml"
xml.write_text("""<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_banner_background"/>
    <foreground android:drawable="@mipmap/ic_banner_foreground"/>
</adaptive-icon>
""",encoding="utf-8")
print("brand:",xml.relative_to(ROOT))
color=RES/"values/ic_launcher_background.xml"
color.write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources><color name="ic_launcher_background">#041428</color></resources>
""",encoding="utf-8")
color=RES/"values/ic_banner_background.xml"
color.write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources><color name="ic_banner_background">#041428</color></resources>
""",encoding="utf-8")
