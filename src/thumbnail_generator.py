import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

# Channel palette
BG    = (13, 13, 26)
GOLD  = (255, 209, 102)
TEAL  = (6, 214, 160)
WHITE = (255, 255, 255)

FONT_PATHS = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def _load_font(size):
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_thumbnail(title, output_path, background_image_path=None):
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), BG)

    # Geometric decorations matching the Manim channel style
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    # Large gold circle — top-left bleed
    r, cx, cy = 310, -90, -70
    od.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(*GOLD, 70), width=3, fill=(*GOLD, 12))

    # Medium teal circle — bottom-right bleed
    r2, cx2, cy2 = 200, W+50, H+30
    od.ellipse([cx2-r2, cy2-r2, cx2+r2, cy2+r2], outline=(*TEAL, 55), width=2, fill=(*TEAL, 10))

    # Small white circle — top-right
    r3, cx3, cy3 = 75, W-90, 65
    od.ellipse([cx3-r3, cy3-r3, cx3+r3, cy3+r3], outline=(*WHITE, 20), width=1, fill=(*WHITE, 5))

    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Gold accent line
    ly = H // 2 + 35
    draw.line([(W//2 - 270, ly), (W//2 + 270, ly)], fill=GOLD, width=3)

    # Title text
    wrapped = textwrap.fill(title, width=22)
    lines   = wrapped.split("\n")
    font    = _load_font(78 if len(lines) <= 2 else 62)
    lh      = 92 if len(lines) <= 2 else 76
    total_h = len(lines) * lh
    y = (H - total_h) // 2 - 25

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (W - w) // 2
        draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=WHITE)
        y += lh

    img.save(output_path, "JPEG", quality=95)
