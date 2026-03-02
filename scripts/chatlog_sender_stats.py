#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Count messages and total character length for a sender in simplified chatlog JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Count sender messages and total chars")
    parser.add_argument("--inputs", nargs="+", required=True, help="Simplified JSON files")
    parser.add_argument("--sender", required=True, help="Exact senderName to match")
    return parser.parse_args()


def load_json(path: Path) -> List[dict[str, Any]]:
    data = path.read_bytes()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("gb18030")
    if not text.strip():
        return []
    obj = json.loads(text)
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        # Support APIs that wrap data in a top-level object.
        data_list = obj.get("data")
        if isinstance(data_list, list):
            return data_list
    return []


def extract_sender_and_content(item: dict[str, Any]) -> Tuple[str, str]:
    sender = (
        item.get("senderName")
        or item.get("sender_name")
        or item.get("sender")
        or ""
    )
    content = item.get("content") or item.get("Content") or ""
    return str(sender), str(content)


def main() -> int:
    args = parse_args()
    sender = args.sender

    total_msgs = 0
    total_chars = 0

    for input_path in args.inputs:
        path = Path(input_path)
        if not path.exists():
            print(f"Skip missing: {path}")
            continue

        items = load_json(path)
        for item in items:
            item_sender, content = extract_sender_and_content(item)
            if item_sender == sender:
                total_msgs += 1
                total_chars += len(str(content))

    print(f"{sender} 发言次数: {total_msgs}")
    print(f"{sender} 总字数: {total_chars}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
