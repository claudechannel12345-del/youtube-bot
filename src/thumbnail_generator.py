import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
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
    if background_image_path and os.path.exists(background_image_path):
        img = Image.open(background_image_path).convert("RGB").resize((1280, 720), Image.LANCZOS)
    else:
        img = Image.new("RGB", (1280, 720), (20, 20, 60))

    # Semi-transparent dark overlay for text readability
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 150))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    font = _load_font(72)

    wrapped = textwrap.fill(title, width=22)
    lines = wrapped.split("\n")
    line_height = 88
    total_h = len(lines) * line_height
    y = (720 - total_h) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (1280 - w) // 2
        # Drop shadow
        draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0))
        # White text
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += line_height

    img.save(output_path, "JPEG", quality=92)
