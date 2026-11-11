#!/usr/bin/env python3
"""Pack generated sticker images into a WhatsApp-ready sticker set.

Usage:
    python3 pack.py <input-folder> <output-folder> [--name "Pack name"]
                    [--tray FILE] [--margin 16] [--outline 0]
                    [--bg-tolerance 32] [--no-bg-removal]

Input:  a folder of PNG / JPG / WebP images, one sticker each, in natural name
        order (1, 2, ... 10). Best: transparent PNGs. A plain white or flat-colour
        background is removed automatically; a photo, gradient or fake
        checkerboard background is rejected (regenerate those).
Output: <output>/png/NN.png and <output>/webp/NN.webp (512x512, WebP < 100KB),
        <output>/tray.png (96x96, < 50KB), <output>/overview.png (numbered grid).
        Old png/ and webp/ files in the output folder are cleared first.

Exit codes: 0 all good · 1 a sticker breaks a WhatsApp rule or could not be used
            · 2 usage error.
Needs Pillow:  python3 -m pip install pillow
"""
import argparse
import io
import re
import sys
from collections import deque
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    print("Pillow is missing. Run:  python3 -m pip install pillow", file=sys.stderr)
    sys.exit(2)

SIZE = 512
TRAY = 96
MAX_BYTES = 100 * 1024
MAX_TRAY_BYTES = 50 * 1024
MIN_COUNT, MAX_COUNT = 3, 30
EXTS = {".png", ".jpg", ".jpeg", ".webp"}
SKIP_NAMES = {"tray.png", "overview.png"}
REDRAWN_OUTLINE = 8          # px at 512 scale, drawn when a background was removed
MAX_OPAQUE_AFTER_REMOVAL = 0.75
FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "Arial Unicode.ttf",
    "Arial.ttf",
]


class StickerError(Exception):
    pass


def natural_key(p):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.name)]


def has_real_alpha(img):
    """True if the image already has a transparent background (transparent corners)."""
    if img.mode != "RGBA":
        return False
    alpha = img.getchannel("A")
    w, h = img.size
    corners = [alpha.getpixel(p) for p in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]]
    return min(corners) < 16


def opaque_ratio(img):
    hist = img.getchannel("A").histogram()
    return sum(hist[128:]) / (img.width * img.height)


def remove_flat_background(img, tolerance):
    """Flood-fill from the border and make the connected plain background transparent.

    Raises StickerError when the background is not plain enough to remove.
    """
    rgb = img.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    ref = px[0, 0]

    def close(c):
        return all(abs(c[i] - ref[i]) <= tolerance for i in range(3))

    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    mask = Image.new("L", (w, h), 255)
    mp = mask.load()
    while q:
        x, y = q.popleft()
        i = y * w + x
        if seen[i]:
            continue
        seen[i] = 1
        if not close(px[x, y]):
            continue
        mp[x, y] = 0
        if x > 0: q.append((x - 1, y))
        if x < w - 1: q.append((x + 1, y))
        if y > 0: q.append((x, y - 1))
        if y < h - 1: q.append((x, y + 1))
    # drop stray near-background specks and the light fringe, then soften the edge
    mask = mask.filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.MinFilter(3))
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))
    out = rgb.convert("RGBA")
    out.putalpha(mask)
    if opaque_ratio(out) > MAX_OPAQUE_AFTER_REMOVAL:
        raise StickerError("background is not plain (photo, gradient or fake checkerboard). "
                           "Regenerate it with a transparent or plain white background.")
    return out


def add_outline(img, px_width):
    """White outline around the opaque area."""
    if px_width <= 0:
        return img
    grown = img.getchannel("A").filter(ImageFilter.MaxFilter(px_width * 2 + 1))
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    base = Image.composite(white, Image.new("RGBA", img.size, (255, 255, 255, 0)), grown)
    base.alpha_composite(img)
    return base


def fit(img, margin, outline=0):
    """Trim, scale into the 512 box (leaving room for the outline), outline at 512 scale."""
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        raise StickerError("image is fully transparent")
    img = img.crop(bbox)
    box = SIZE - 2 * (margin + outline)
    scale = min(box / img.width, box / img.height)
    img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.alpha_composite(img, ((SIZE - img.width) // 2, (SIZE - img.height) // 2))
    return add_outline(canvas, outline)


def prepare(path, a):
    """Open one input image and return (512x512 RGBA, note)."""
    try:
        img = Image.open(path).convert("RGBA")
    except Exception as e:
        raise StickerError(f"cannot open image ({e})")
    note = ""
    if not has_real_alpha(img):
        if a.no_bg_removal:
            raise StickerError("no transparent background (and --no-bg-removal is set)")
        img = remove_flat_background(img, a.bg_tolerance)
        note = "  [background removed, outline redrawn: check the edges]"
    outline = a.outline if a.outline > 0 else (REDRAWN_OUTLINE if note else 0)
    return fit(img, a.margin, outline), note


def save_webp_under_limit(img, path):
    for q in range(90, 19, -5):
        buf = io.BytesIO()
        img.save(buf, "WEBP", quality=q, method=6, alpha_quality=max(q, 60))
        if buf.tell() <= MAX_BYTES:
            break
    path.write_bytes(buf.getvalue())
    return buf.tell(), q


def load_font(size):
    for f in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def overview(stickers, path, title):
    cols, cell, label = 4, 256, 36
    rows = (len(stickers) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + label) + 60), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    font = load_font(28)
    draw.text((16, 14), title, fill="white", font=font)
    for i, (name, img) in enumerate(stickers):
        x, y = (i % cols) * cell, 60 + (i // cols) * (cell + label)
        tile = Image.new("RGB", (cell - 8, cell - 8), (235, 235, 235))
        thumb = img.resize((cell - 8, cell - 8), Image.LANCZOS)
        tile.paste(thumb, (0, 0), thumb)
        sheet.paste(tile, (x + 4, y))
        draw.text((x + 8, y + cell - 4), name, fill="white", font=font)
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--name", default="Sticker pack")
    ap.add_argument("--tray", help="image for the tray icon (default: the first sticker)")
    ap.add_argument("--margin", type=int, default=16, help="empty border in px, 0 to 128 (default 16)")
    ap.add_argument("--outline", type=int, default=0,
                    help="white outline in px, 0 to 32 (default: none, or 8 when a background was removed)")
    ap.add_argument("--bg-tolerance", type=int, default=32)
    ap.add_argument("--no-bg-removal", action="store_true")
    a = ap.parse_args()

    src, out = Path(a.input).resolve(), Path(a.output).resolve()
    if not src.is_dir():
        print(f"Input folder not found: {src}", file=sys.stderr); return 2
    if src == out:
        print("Output folder must be different from the input folder.", file=sys.stderr); return 2
    if not 0 <= a.margin <= 128:
        print("--margin must be between 0 and 128.", file=sys.stderr); return 2
    if not 0 <= a.outline <= 32:
        print("--outline must be between 0 and 32.", file=sys.stderr); return 2
    if a.tray and not Path(a.tray).is_file():
        print(f"Tray image not found: {a.tray}", file=sys.stderr); return 2

    files = sorted((p for p in src.iterdir()
                    if p.suffix.lower() in EXTS and not p.name.startswith(".") and p.name not in SKIP_NAMES),
                   key=natural_key)
    if not files:
        print(f"No images found in {src}", file=sys.stderr); return 2

    for sub in ("png", "webp"):
        d = out / sub
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("*." + sub):
            old.unlink()

    problems, stickers = [], []
    for f in files:
        try:
            img, note = prepare(f, a)
        except StickerError as e:
            problems.append(f"{f.name}: {e}")
            print(f"SKIP   {f.name}  {e}")
            continue
        name = f"{len(stickers) + 1:02d}"
        img.save(out / "png" / f"{name}.png")
        size, q = save_webp_under_limit(img, out / "webp" / f"{name}.webp")
        if size > MAX_BYTES:
            problems.append(f"{f.name}: WebP is still {size // 1024}KB at the lowest quality (limit 100KB)")
        flag = "OK " if size <= MAX_BYTES else "BIG"
        print(f"{flag} {name} <- {f.name}  {size // 1024}KB q{q}{note}")
        stickers.append((name, img))

    if stickers:
        try:
            tray_img = prepare(Path(a.tray), a)[0] if a.tray else stickers[0][1]
            tray_img.resize((TRAY, TRAY), Image.LANCZOS).save(out / "tray.png", optimize=True)
            if (out / "tray.png").stat().st_size > MAX_TRAY_BYTES:
                problems.append("tray.png is over 50KB")
        except StickerError as e:
            problems.append(f"tray image: {e}")
        overview(stickers, out / "overview.png", f"{a.name} / {len(stickers)} stickers")

    count = len(stickers)
    if not MIN_COUNT <= count <= MAX_COUNT:
        problems.append(f"pack has {count} usable stickers; WhatsApp needs {MIN_COUNT} to {MAX_COUNT} per pack")

    print(f"\n{count} stickers -> {out}")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("All stickers meet WhatsApp's rules. Now open overview.png and look at every sticker yourself.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
