#!/usr/bin/env python3
"""
Script to create a simple icon for Windows 11 Workspace Manager
Creates a 256x256 icon with multiple sizes embedded
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_workspace_icon():
    """Create a modern workspace icon"""

    # Create base image (256x256)
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Modern color scheme (Windows 11 style)
    bg_color = (0, 120, 212)  # Windows blue
    accent_color = (255, 255, 255)  # White
    shadow_color = (0, 90, 158)  # Darker blue

    # Draw rounded square background with gradient effect
    padding = 20
    corner_radius = 40

    # Shadow layer
    draw.rounded_rectangle(
        [(padding + 4, padding + 4), (size - padding + 4, size - padding + 4)],
        radius=corner_radius,
        fill=shadow_color
    )

    # Main background
    draw.rounded_rectangle(
        [(padding, padding), (size - padding, size - padding)],
        radius=corner_radius,
        fill=bg_color
    )

    # Draw 4 smaller squares representing windows/workspaces
    grid_padding = 60
    square_size = 60
    gap = 20

    positions = [
        (grid_padding, grid_padding),  # Top-left
        (grid_padding + square_size + gap, grid_padding),  # Top-right
        (grid_padding, grid_padding + square_size + gap),  # Bottom-left
        (grid_padding + square_size + gap, grid_padding + square_size + gap),  # Bottom-right
    ]

    for i, (x, y) in enumerate(positions):
        # Add slight variation to make it interesting
        alpha = 255 if i < 3 else 180  # Last one slightly transparent
        color = accent_color + (alpha,)

        draw.rounded_rectangle(
            [(x, y), (x + square_size, y + square_size)],
            radius=10,
            fill=color
        )

    # Save as PNG first
    png_path = "assets/icon.png"
    os.makedirs("assets", exist_ok=True)
    img.save(png_path, "PNG")
    print(f"[OK] Created PNG icon: {png_path}")

    # Create ICO with multiple sizes
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]

    # Create list of images at different sizes
    images = []
    for icon_size in icon_sizes:
        resized = img.resize(icon_size, Image.Resampling.LANCZOS)
        images.append(resized)

    # Save as ICO
    ico_path = "assets/icon.ico"
    images[0].save(
        ico_path,
        format='ICO',
        sizes=[img.size for img in images],
        append_images=images[1:]
    )
    print(f"[OK] Created ICO icon: {ico_path}")

    print(f"\nIcon created successfully!")
    print(f"  - PNG: {png_path} (for preview)")
    print(f"  - ICO: {ico_path} (for Windows)")
    print(f"\nNow you can:")
    print(f"  1. Uncomment 'SetupIconFile' line in installer.iss")
    print(f"  2. Rebuild the installer with Inno Setup")
    print(f"  3. Rebuild the EXE with: python build.py")

if __name__ == "__main__":
    print("Creating Workspace Manager icon...\n")
    create_workspace_icon()
