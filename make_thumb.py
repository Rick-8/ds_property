"""
make_thumb.py

Utility script to create a square, center-cropped thumbnail (default 60x60 px)
from an existing image file, using the Pillow library. The thumbnail is saved
as a JPEG for use in cards, icons, or anywhere a small, uniform image
is needed.

Usage:
    - Adjust input_image and output_image paths as needed.
    - Run: python make_thumb.py
    - The thumbnail will be saved to the specified output path.

Requirements:
    - Pillow
"""

from PIL import Image
import os


def make_square_thumbnail(input_path, output_path, size=60):
    """
    Create a square, center-cropped thumbnail of an image and save as JPEG.

    Args:
        input_path (str): Path to the original image file.
        output_path (str): Path to save the resulting thumbnail.
        size (int): Width and height of the square thumbnail in pixels.

    The function crops the image to a square from the center, resizes it to
    (size x size), and saves it as a JPEG for web use.
    """
    img = Image.open(input_path)
    img = img.convert("RGB")
    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    img = img.crop((left, top, right, bottom))
    img = img.resize((size, size), Image.LANCZOS)
    img.save(output_path, "JPEG", quality=85)
    print(f"Thumbnail saved: {output_path}")


input_image = "home\static\media\Digital_Glyph_Green.png"
output_image = "static/media/thumbnails/Digital_Glyph_Green-thumb.png"
make_square_thumbnail(input_image, output_image)
