#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract all messages from a sender across exports, excluding recall/system recall messages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract sender messages excluding recalls")
    parser.add_argument("--inputs", nargs="+", required=True, help="Original JSON files")
    parser.add_argument("--sender", required=True, help="Exact senderName to match")
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
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
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


def extract_time(item: dict[str, Any]) -> Any:
    return item.get("time") or item.get("Time") or ""


def format_time_to_minute(value: Any) -> str:
    if not value:
        return ""
    text = str(value)
    try:
        dt = datetime.fromisoformat(text)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return text[:16].replace("T", " ")


def is_recall(content: str) -> bool:
    c = content.strip()
    if not c:
        return False
    recall_keywords = [
        "撤回",
        "撤回了一条消息",
        "撤回了",
        "recalled",
        "recall",
    ]
    return any(k in c for k in recall_keywords)


def main() -> int:
    args = parse_args()
    sender = args.sender

    results: List[dict[str, Any]] = []

    for input_path in args.inputs:
        path = Path(input_path)
        if not path.exists():
            print(f"Skip missing: {path}")
            continue

        items = load_json(path)
        for item in items:
            item_sender, content = extract_sender_and_content(item)
            if item_sender != sender:
                continue
            if is_recall(str(content)):
                continue

            results.append({
                "senderName": item_sender,
                "time": extract_time(item),
                "content": content,
            })

    out_json = Path(args.out_json)
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8-sig")

    out_md = Path(args.out_md)
    lines: List[str] = []
    lines.append(f"# Messages: {sender}")
    lines.append("")

    for item in results:
        time = format_time_to_minute(item.get("time", ""))
        content = item.get("content", "")
        lines.append(f"## {time}  **{sender}**")
        lines.append(str(content))
        lines.append("")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")

    print(f"Total: {len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
