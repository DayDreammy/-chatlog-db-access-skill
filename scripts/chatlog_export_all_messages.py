#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Export all messages across multiple exports to JSON + Markdown."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, List, Dict, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export all messages to JSON + Markdown")
    parser.add_argument("--inputs", nargs="+", required=True, help="Original JSON files")
    parser.add_argument("--out-json", required=True, help="Output JSON path")
    parser.add_argument("--out-md", required=True, help="Output Markdown path")
    parser.add_argument("--image-dir", default="", help="Directory containing decoded JPG images")
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


def extract_sender(item: dict[str, Any]) -> str:
    sender = (
        item.get("senderName")
        or item.get("sender_name")
        or item.get("sender")
        or ""
    )
    sender = str(sender).strip()
    return sender if sender else "(system)"


def extract_content(item: dict[str, Any]) -> str:
    return str(item.get("content") or item.get("Content") or "")


def extract_time(item: dict[str, Any]) -> str:
    return str(item.get("time") or item.get("Time") or "")

def extract_group(item: dict[str, Any]) -> str:
    group = item.get("talkerName") or item.get("talker_name") or ""
    group = str(group).strip()
    return group if group else "Unknown Group"


def is_recall(content: str) -> bool:
    c = content.strip().lower()
    if not c:
        return False
    recall_keywords = [
        "撤回",
        "撤回了一条消息",
        "撤回了",
        "recalled a message",
        "recalled",
        "recall",
    ]
    return any(k in c for k in recall_keywords)


def is_empty_system_notice(item: dict[str, Any], content: str) -> bool:
    msg_type = item.get("type")
    sender = extract_sender(item)
    contents = item.get("contents")
    if msg_type == 10000 and sender in {"系统消息", "(system)", ""} and not content.strip() and not contents:
        return True
    return False


def is_empty_text_message(item: dict[str, Any], content: str) -> bool:
    # Drop empty text-type messages (type=47) with no content/structured payloads.
    if item.get("type") == 47 and not content.strip() and not item.get("contents"):
        return True
    return False


def format_time_to_minute(value: str) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return value[:16].replace("T", " ")


def sanitize_md_content(text: str) -> str:
    # Remove repeated '?' sequences (2+)
    text = re.sub(r"\?{2,}", "", text)
    # Remove trailing '?' in mentions like @name?
    text = re.sub(r"(@\\S+)\\?", r"\\1", text)
    return text


def apply_soft_line_breaks(text: str) -> str:
    # Convert single line breaks into blank-line breaks for safer Markdown rendering.
    lines = text.splitlines()
    return "\n\n".join(lines) if lines else text


def render_content(item: dict[str, Any], image_dir: Optional[Path], md_dir: Optional[Path]) -> str:
    content = extract_content(item).strip()
    contents = item.get("contents") or {}

    # If message has a reference, append it under a separator.
    refer = contents.get("refer") if isinstance(contents, dict) else None
    if content:
        if isinstance(refer, dict):
            r_sender = refer.get("senderName") or refer.get("sender") or ""
            r_content = refer.get("content") or ""
            ref_line = f"{r_sender}:{r_content}".strip(":")
            if ref_line:
                return content + "\n\n引用：" + ref_line
        return content
    contents = item.get("contents") or {}

    # Image messages: try to map to decoded JPG in image_dir.
    if image_dir and isinstance(contents, dict):
        imgfile = contents.get("imgfile") or ""
        thumb = contents.get("thumb") or ""
        img_stem = Path(str(imgfile)).stem if imgfile else ""
        thumb_stem = Path(str(thumb)).stem if thumb else ""

        # Prefer full image, fall back to thumb even if imgfile exists.
        if img_stem:
            jpg = image_dir / f"{img_stem}.jpg"
            if jpg.exists():
                rel = jpg
                if md_dir:
                    rel = Path(os.path.relpath(jpg, md_dir))
                return f"![image]({rel.as_posix()})"

        if thumb_stem:
            thumb_jpg = image_dir / "thumbs" / f"{thumb_stem}.jpg"
            if thumb_jpg.exists():
                rel = thumb_jpg
                if md_dir:
                    rel = Path(os.path.relpath(thumb_jpg, md_dir))
                return f"![image]({rel.as_posix()})"

    # Fallbacks for structured messages (cards, references, etc.)
    if isinstance(contents, dict):
        # Group announcement (type=49, subType=87)
        if item.get("type") == 49 and item.get("subType") == 87:
            return "【群公告】"

        # Video channel card (type=49, subType=51)
        if item.get("type") == 49 and item.get("subType") == 51:
            title = contents.get("title") or ""
            if title:
                return f"[视频号] {title}"
            return "[视频号]"

        title = contents.get("title") or ""
        url = contents.get("url") or ""
        if title or url:
            return f"[Card] {title} {url}".strip()

        refer = contents.get("refer")
        if isinstance(refer, dict):
            r_sender = refer.get("senderName") or refer.get("sender") or ""
            r_content = refer.get("content") or ""
            ref_line = f"{r_sender}:{r_content}".strip(":")
            if ref_line:
                return "引用：" + ref_line

    msg_type = item.get("type")
    sub_type = item.get("subType")
    # For empty text-type messages, return empty so they can be filtered out.
    if msg_type == 47 and not content:
        return ""
    # If it's an image message but missing files, show a friendly placeholder.
    if msg_type == 3 and sub_type == 0 and not content:
        return "【图片消息】"
    if msg_type == 34 and sub_type == 0:
        return "【语音消息】"
    if msg_type == 48 and sub_type == 0:
        return "【地图消息】"
    if msg_type == 42:
        return "【公众号卡片】"
    # If it's a system message with no content, drop it.
    if msg_type == 10000 and not content:
        return ""
    if msg_type == 49:
        return "【其他类型消息】"
    return f"[Non-text message] type={msg_type} subType={sub_type}"


def main() -> int:
    args = parse_args()

    results: List[dict[str, Any]] = []
    image_dir = Path(args.image_dir) if args.image_dir else None
    md_dir = Path(args.out_md).resolve().parent

    for input_path in args.inputs:
        path = Path(input_path)
        if not path.exists():
            print(f"Skip missing: {path}")
            continue
        items = load_json(path)
        for item in items:
            content = render_content(item, image_dir, md_dir)
            if is_recall(content):
                continue
            if is_empty_system_notice(item, content):
                continue
            if is_empty_text_message(item, content):
                continue
            results.append({
                "senderName": extract_sender(item),
                "time": extract_time(item),
                "content": content,
                "type": item.get("type"),
                "subType": item.get("subType"),
                "contents": item.get("contents", None),
                "group": extract_group(item),
            })

    out_json = Path(args.out_json)
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8-sig")

    out_md = Path(args.out_md)
    lines: List[str] = []
    groups: Dict[str, List[dict[str, Any]]] = {}
    for item in results:
        groups.setdefault(item.get("group", "Unknown Group"), []).append(item)

    for group_name, items in groups.items():
        lines.append(f"# {group_name}")
        lines.append("")
        for item in items:
            time = format_time_to_minute(item.get("time", ""))
            sender = item.get("senderName", "(system)")
            content = sanitize_md_content(str(item.get("content", "")))
            content = apply_soft_line_breaks(content)
            lines.append(f"## {time}  **{sender}**")
            lines.append("")
            lines.append(str(content))
            lines.append("")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")

    print(f"Total: {len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
