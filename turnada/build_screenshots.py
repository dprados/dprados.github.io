#!/usr/bin/env python3
"""Turn the framed store screenshots into light web images for the landing.

Reads   <src>/<es-ES|en-US|de-DE>/iphone69_<1..6>.png   (1320x2868)
Writes  turnada/screenshots/<es|en|de>/<1..6>.webp      (600 px wide)

Usage (from anywhere):
  /Users/diegoprados/Developer/Personal/TodaysApp/.venv/bin/python turnada/build_screenshots.py [src_dir]

Default src_dir: ../../../apps/turnada/store/screenshots/ios relative to this file's folder
(i.e. TodaysApp/apps/turnada/store/screenshots/ios). Needs Pillow with WebP support.
"""
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
DEFAULT_SRC = HERE.parents[2] / "apps" / "turnada" / "store" / "screenshots" / "ios"
LOCALES = {"es-ES": "es", "en-US": "en", "de-DE": "de"}
WIDTH = 600

src = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_SRC
missing, made = [], 0
for locale, short in LOCALES.items():
    out_dir = HERE / "screenshots" / short
    out_dir.mkdir(parents=True, exist_ok=True)
    for n in range(1, 7):
        png = src / locale / f"iphone69_{n}.png"
        if not png.exists():
            missing.append(str(png))
            continue
        im = Image.open(png).convert("RGB")
        h = round(im.height * WIDTH / im.width)
        im = im.resize((WIDTH, h), Image.LANCZOS)
        im.save(out_dir / f"{n}.webp", "WEBP", quality=82, method=6)
        made += 1

print(f"{made} screenshots written to {HERE / 'screenshots'}")
if missing:
    print(f"{len(missing)} missing source files, e.g. {missing[0]}")
    sys.exit(1 if made == 0 else 0)
