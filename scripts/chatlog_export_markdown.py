#!/usr/bin/env python
r"""
Convert simplified chatlog JSON to readable Markdown.

Example:
  python chatlog_export_markdown.py \
    --inputs D:\exports\xxx_simple.json D:\exports\yyy_simple.json \
    --out-dir D:\exports
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export simplified chatlog JSON to Markdown")
    parser.add_argument("--inputs", nargs="+", required=True, help="Input simplified JSON files")
    parser.add_argument("--out-dir", default="./exports", help="Output directory for Markdown files")
    return parser.parse_args()


def parse_time(value: str) -> datetime:
    # ISO 8601 with timezone or naive; fallback to original string order on failure
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return datetime.min


def normalize_sender(name: Any) -> str:
    if name is None:
        return "(system)"
    text = str(name).strip()
    return text if text else "(system)"


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for input_path in args.inputs:
        in_path = Path(input_path)
        if not in_path.exists():
            print(f"Skip missing: {in_path}")
            continue

        data = in_path.read_bytes()
        try:
            raw = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            # Fallback for Windows JSON exports that may be GBK/GB18030.
            raw = data.decode("gb18030")
        items: List[dict[str, Any]] = json.loads(raw) if raw.strip() else []
        if not items:
            continue

        items_sorted = sorted(items, key=lambda x: parse_time(str(x.get("time", ""))))

        base_name = in_path.stem
        out_path = out_dir / f"{base_name}.md"

        lines: List[str] = []
        lines.append("# Chatlog Backup")
        lines.append("")
        lines.append(f"Source: {base_name}")
        lines.append("")

        for item in items_sorted:
            time = item.get("time", "")
            sender = normalize_sender(item.get("senderName"))
            content = item.get("content", "")
            msg_id = item.get("id", "")

            if msg_id:
                lines.append(f"- [{time}] **{sender}**: {content}  `id:{msg_id}`")
            else:
                lines.append(f"- [{time}] **{sender}**: {content}")

        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
