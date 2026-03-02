#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert Markdown to Word (docx) with resource-path for images."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert Markdown to Word with resource-path")
    parser.add_argument("--md", required=True, help="Input Markdown file")
    parser.add_argument("--out", required=True, help="Output DOCX file")
    parser.add_argument("--resource-path", required=True, help="Resource path for images")
    parser.add_argument("--pandoc", default="pandoc", help="Pandoc path or command name in PATH")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pandoc = Path(args.pandoc)
    # Allow either an absolute path or a command available in PATH.
    if pandoc.name == str(pandoc) and "\\" not in str(pandoc) and "/" not in str(pandoc):
        cmd = [
            args.pandoc,
            args.md,
            "-o",
            args.out,
            "--resource-path",
            args.resource_path,
        ]
        subprocess.run(cmd, check=True)
        print(f"done: {args.out}")
        return 0

    if not pandoc.exists():
        raise SystemExit(f"Pandoc not found: {pandoc}")

    cmd = [
        str(pandoc),
        args.md,
        "-o",
        args.out,
        "--resource-path",
        args.resource_path,
    ]
    subprocess.run(cmd, check=True)
    print(f"done: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
