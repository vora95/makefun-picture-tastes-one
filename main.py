#!/usr/bin/env python3
"""The picture that tastes of one ingredient.

Entry program for make.fun's "The picture that tastes of one ingredient"
bounty. Writes one image of food — a single ripe strawberry, the one
ingredient this picture tastes of — to /output/entry.png.

The image is generated procedurally by generate_image.py (PIL + numpy, no
photos, no network) and shipped in this repository as entry.png; this
program copies it to /output/entry.png deterministically (stdlib only, so
it runs in the grading sandbox with no network and no third-party packages).
The output is a JPEG (1024x1024, < 1 MiB) stored under the name entry.png,
as the competition rules allow (PNG or JPEG, told apart by magic bytes).
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _jpeg_dimensions(path):
    """Read (width, height) from a JPEG's SOF0/SOF2 marker (stdlib only)."""
    with open(path, "rb") as f:
        data = f.read()
    i = 2
    while i < len(data) - 1:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC2):
            height = int.from_bytes(data[i + 5:i + 7], "big")
            width = int.from_bytes(data[i + 7:i + 9], "big")
            return width, height
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg_len = int.from_bytes(data[i + 2:i + 4], "big")
        i += 2 + seg_len
    raise ValueError("no SOF marker found")


def main() -> int:
    src = os.path.join(HERE, "entry.png")
    out_dir = "/output"
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    with open(src, "rb") as f:
        magic = f.read(3)
    if magic[:2] != b"\xff\xd8":
        raise SystemExit("entry.png is not a JPEG")
    width, height = _jpeg_dimensions(src)
    if (width, height) != (1024, 1024):
        raise SystemExit(f"entry.png is {width}x{height}, need 1024x1024")
    shutil.copyfile(src, dst)
    size = os.path.getsize(dst)
    if size > 1_048_576:
        raise SystemExit(f"output too large: {size} bytes")
    print(f"wrote {dst} ({size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
