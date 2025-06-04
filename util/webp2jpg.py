#!/usr/bin/env python3
"""
Convert WebP images to JPEG format
"""
import argparse
import pathlib
from PIL import Image
import sys


def convert_webp_to_jpg(webp_path, output_dir=None, quality=95, remove_original=False):
    """Convert a single WebP image to JPEG."""
    try:
        # Open the WebP image
        img = Image.open(webp_path)

        # Convert RGBA to RGB if necessary (JPEG doesn't support transparency)
        if img.mode in ("RGBA", "LA", "P"):
            # Create a white background
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            # Paste the image on the white background using alpha channel as mask
            if img.mode == "P":
                img = img.convert("RGBA")
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = rgb_img

        # Determine output path
        if output_dir:
            output_path = output_dir / (webp_path.stem + ".jpg")
        else:
            output_path = webp_path.with_suffix(".jpg")

        # Save as JPEG
        img.save(output_path, "JPEG", quality=quality, optimize=True)

        # Remove original if requested
        if remove_original:
            webp_path.unlink()

        return True, output_path

    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Convert WebP images to JPEG")
    parser.add_argument(
        "path", type=str, help="Directory containing WebP files or single WebP file"
    )
    parser.add_argument(
        "-o", "--output", type=str, help="Output directory (default: same as input)"
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=95,
        help="JPEG quality (1-100, default: 95)",
    )
    parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Remove original WebP files after conversion",
    )
    parser.add_argument(
        "--recursive", action="store_true", help="Process subdirectories recursively"
    )

    args = parser.parse_args()

    input_path = pathlib.Path(args.path)

    if not input_path.exists():
        print(f"Error: {input_path} does not exist")
        sys.exit(1)

    # Set up output directory
    output_dir = pathlib.Path(args.output) if args.output else None
    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # Collect WebP files
    webp_files = []
    if input_path.is_file() and input_path.suffix.lower() == ".webp":
        webp_files = [input_path]
    elif input_path.is_dir():
        pattern = "**/*.webp" if args.recursive else "*.webp"
        webp_files = list(input_path.glob(pattern))
        # Also check for .WEBP (uppercase)
        webp_files.extend(list(input_path.glob(pattern.replace("webp", "WEBP"))))
    else:
        print(f"Error: {input_path} is not a WebP file or directory")
        sys.exit(1)

    if not webp_files:
        print("No WebP files found")
        sys.exit(0)

    print(f"Found {len(webp_files)} WebP file(s)")

    # Convert files
    success_count = 0
    error_count = 0

    for i, webp_path in enumerate(webp_files, 1):
        print(f"[{i}/{len(webp_files)}] Converting {webp_path.name}...", end=" ")

        # If output directory is specified, maintain relative structure
        if output_dir and input_path.is_dir():
            relative_path = webp_path.relative_to(input_path)
            file_output_dir = output_dir / relative_path.parent
            file_output_dir.mkdir(parents=True, exist_ok=True)
        else:
            file_output_dir = output_dir

        success, result = convert_webp_to_jpg(
            webp_path, file_output_dir, args.quality, args.remove
        )

        if success:
            print(f"✓ → {result.name}")
            success_count += 1
        else:
            print(f"✗ Error: {result}")
            error_count += 1

    # Summary
    print(f"\nConversion complete!")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {error_count}")

    if args.remove and success_count > 0:
        print(f"  Removed {success_count} original WebP file(s)")


if __name__ == "__main__":
    main()
