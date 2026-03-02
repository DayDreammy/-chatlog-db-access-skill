#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Filter exported messages JSON by sender or senderName and regenerate Markdown."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, List, Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Filter export by sender/senderName")
    parser.add_argument("--in-json", required=True, help="Input JSON from export_all_messages")
    parser.add_argument("--sender", required=True, help="Exact sender or senderName to match")
    parser.add_argument("--out-json", required=True, help="Output JSON path")
    parser.add_argument("--out-md", required=True, help="Output Markdown path")
    return parser.parse_args()


def load_json(path: Path) -> List[dict[str, Any]]:
    data = path.read_bytes()
    text = None
    for enc in ("utf-8-sig", "utf-16", "utf-16le", "utf-16be", "gb18030"):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = data.decode("utf-8", errors="replace")
    if not text.strip():
        return []
    obj = json.loads(text)
    return obj if isinstance(obj, list) else []


def format_time_to_minute(value: str) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return value[:16].replace("T", " ")


def sanitize_md_content(text: str) -> str:
    text = re.sub(r"\?{2,}", "", text)
    text = re.sub(r"(@\S+)\?", r"\1", text)
    return "\n\n".join(text.splitlines()) if text else text


def main() -> int:
    args = parse_args()
    sender = args.sender

    items = load_json(Path(args.in_json))
    filtered = [
        m for m in items
        if m.get("senderName") == sender or m.get("sender") == sender
    ]

    out_json = Path(args.out_json)
    out_json.write_text(json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8-sig")

    groups: Dict[str, List[dict[str, Any]]] = {}
    for item in filtered:
        groups.setdefault(item.get("group", "Unknown Group"), []).append(item)

    lines: List[str] = []
    for group_name, items_in_group in groups.items():
        lines.append(f"# {group_name}")
        lines.append("")
        for item in items_in_group:
            time = format_time_to_minute(item.get("time", ""))
            content = sanitize_md_content(str(item.get("content", "")))
            lines.append(f"## {time}  **{sender}**")
            lines.append("")
            lines.append(content)
            lines.append("")

    out_md = Path(args.out_md)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")

    print(f"Total: {len(filtered)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
