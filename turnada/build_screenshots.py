#!/usr/bin/env python3
"""Build the landing's images from the app's real screens and widgets.

1. App screens (raw device screenshots, no marketing frame):
   reads   apps/turnada/store/screenshots/raw/ios/<es-ES|en-US|de-DE>/iphone69_<1..6>.png  (1320x2868)
   writes  turnada/screenshots/<es|en|de>/app-<1..6>.webp                                  (640 px wide)
   1 calendar · 2 pay summary · 3 hours balance · 4 day sheet · 5 partner overlay · 6 bonuses and wage

2. Widgets, rendered from the real SwiftUI widget views by the `TurnadaWidgetRender` scheme
   (ios/TurnadaWidgetRenderTests, run once per language with TEST_RUNNER_WIDGET_RENDER_DIR=<store/widgets>/<lang>):
   reads   apps/turnada/store/widgets/<es|en|de>/<light|dark>/<today|week|month|money|lock>.png  (@3x, rounded)
   writes  apps/turnada/store/widgets/<es|en|de>/home_<light|dark>.png   (home screen: wallpaper + 4 widgets)
           apps/turnada/store/widgets/<es|en|de>/lock_<light|dark>.png   (lock screen accessory on a wallpaper)
           turnada/screenshots/<es|en|de>/widget-<name>[-dark].webp, widgets-home[-dark].webp, widgets-lock[-dark].webp

Usage (from anywhere):
  /Users/diegoprados/Developer/Personal/TodaysApp/.venv/bin/python turnada/build_screenshots.py
Needs Pillow with WebP support.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
APP = HERE.parents[2] / "apps" / "turnada"
RAW = APP / "store" / "screenshots" / "raw" / "ios"
WIDGETS = APP / "store" / "widgets"
LOCALES = {"es-ES": "es", "en-US": "en", "de-DE": "de"}
SCREEN_W = 640
S = 3  # widget renders are @3x

made, missing = 0, []


def save_webp(im, path, width=None, quality=82):
    global made
    if width and im.width != width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(path, "WEBP", quality=quality, method=6)
    made += 1


def font(size, bold=True):
    for p in ("/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try:
            f = ImageFont.truetype(p, size)
            if bold and p.endswith("SFNS.ttf"):
                try:
                    f.set_variation_by_name("Semibold")
                except Exception:
                    pass
            return f
        except OSError:
            continue
    return ImageFont.load_default()


def wallpaper(w, h, dark):
    """Soft diagonal gradient in the brand colours (indigo → violet → warm orange)."""
    stops = ([(0.0, (24, 26, 74)), (0.55, (58, 38, 120)), (1.0, (120, 70, 40))] if dark
             else [(0.0, (92, 98, 220)), (0.5, (150, 120, 230)), (1.0, (246, 178, 120))])
    small = Image.new("RGB", (64, 140))
    px = small.load()
    for y in range(small.height):
        for x in range(small.width):
            t = min(1.0, max(0.0, (y / small.height) * 0.8 + (x / small.width) * 0.2))
            for (a, ca), (b, cb) in zip(stops, stops[1:]):
                if a <= t <= b:
                    k = (t - a) / (b - a)
                    px[x, y] = tuple(round(ca[i] + (cb[i] - ca[i]) * k) for i in range(3))
                    break
    return small.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))


def paste_with_shadow(canvas, im, xy, radius=18, opacity=70):
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    alpha = im.getchannel("A").point(lambda a: a * opacity // 255)
    blk = Image.new("RGBA", im.size, (0, 0, 0, 255))
    blk.putalpha(alpha)
    shadow.paste(blk, (xy[0], xy[1] + radius // 2), blk)
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius)))
    canvas.alpha_composite(im, xy)


def status_bar(canvas, dark_text=False):
    d = ImageDraw.Draw(canvas)
    d.text((54 * S, 18 * S), "09:41", font=font(17 * S), fill=(20, 21, 42) if dark_text else (255, 255, 255))


def home_screen(lang, scheme):
    src = WIDGETS / lang / scheme
    w = {n: Image.open(src / f"{n}.png").convert("RGBA") for n in ("today", "money", "week", "month")}
    W, H = 440 * S, 956 * S
    canvas = wallpaper(W, H, scheme == "dark").convert("RGBA")
    status_bar(canvas)
    x0, gap = 38 * S, 24 * S
    y = 78 * S
    paste_with_shadow(canvas, w["today"], (x0, y))
    paste_with_shadow(canvas, w["money"], (x0 + w["today"].width + gap, y))
    y += w["today"].height + gap
    paste_with_shadow(canvas, w["week"], (x0, y))
    y += w["week"].height + gap
    paste_with_shadow(canvas, w["month"], (x0, y))
    # Page dots.
    d = ImageDraw.Draw(canvas)
    cy = (y + w["month"].height + H) // 2
    for i, a in enumerate((255, 110)):
        cx = W // 2 + (i * 2 - 1) * 8 * S
        d.ellipse((cx - 3 * S, cy - 3 * S, cx + 3 * S, cy + 3 * S), fill=(255, 255, 255, a))
    return canvas


def lock_screen(lang, scheme):
    lock = Image.open(WIDGETS / lang / scheme / "lock.png").convert("RGBA")
    W, H = 440 * S, 260 * S
    canvas = wallpaper(W, H * 3, scheme == "dark").crop((0, 0, W, H)).convert("RGBA")
    d = ImageDraw.Draw(canvas)
    big = font(96 * S)
    tw = d.textlength("9:41", font=big)
    d.text(((W - tw) / 2, 34 * S), "9:41", font=big, fill=(255, 255, 255, 235))
    # The accessory sits under the clock, as on the lock screen.
    canvas.alpha_composite(lock, ((W - lock.width) // 2, 176 * S))
    return canvas


def main():
    for locale, short in LOCALES.items():
        out = HERE / "screenshots" / short
        out.mkdir(parents=True, exist_ok=True)
        for n in range(1, 7):
            png = RAW / locale / f"iphone69_{n}.png"
            if not png.exists():
                missing.append(str(png))
                continue
            save_webp(Image.open(png).convert("RGB"), out / f"app-{n}.webp", SCREEN_W)

        if not (WIDGETS / short / "light" / "today.png").exists():
            missing.append(str(WIDGETS / short / "light"))
            continue
        for scheme in ("light", "dark"):
            sfx = "-dark" if scheme == "dark" else ""
            home = home_screen(short, scheme)
            home.convert("RGB").save(WIDGETS / short / f"home_{scheme}.png", optimize=True)
            save_webp(home.convert("RGB"), out / f"widgets-home{sfx}.webp", SCREEN_W)
            lock = lock_screen(short, scheme)
            lock.convert("RGB").save(WIDGETS / short / f"lock_{scheme}.png", optimize=True)
            save_webp(lock.convert("RGB"), out / f"widgets-lock{sfx}.webp", 440)
            # Single widgets at @2x, transparent corners.
            for name in ("today", "week", "month", "money"):
                im = Image.open(WIDGETS / short / scheme / f"{name}.png").convert("RGBA")
                save_webp(im, out / f"widget-{name}{sfx}.webp", im.width * 2 // 3, quality=86)

    print(f"{made} images written to {HERE / 'screenshots'}")
    if missing:
        print(f"{len(missing)} missing sources, e.g. {missing[0]}")
        sys.exit(1 if made == 0 else 0)


if __name__ == "__main__":
    main()
