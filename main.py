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


def main() -> int:
    src = os.path.join(HERE, "entry.png")
    out_dir = "/output"
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    with open(src, "rb") as f:
        magic = f.read(3)
    if magic[:2] != b"\xff\xd8":
        raise SystemExit("entry.png is not a JPEG")
    shutil.copyfile(src, dst)
    size = os.path.getsize(dst)
    if size > 1_048_576:
        raise SystemExit(f"output too large: {size} bytes")
    print(f"wrote {dst} ({size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
