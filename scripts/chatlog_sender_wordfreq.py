#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Word frequency for a specific sender across chatlog JSON exports."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, List, Tuple

import jieba
from wordcloud import WordCloud


STOPWORDS = {
    "的","了","是","我","你","他","她","它","我们","你们","他们","她们","它们",
    "这","那","一个","两个","没有","不是","就是","还是","以及","如果","因为","所以",
    "可以","可能","已经","会","要","去","来","上","下","中","为","与","及",
    "对","等","把","被","并","或","而","也","还","都","就","很","更","最",
    "啊","呢","吧","呀","哦","哈","嗯","嘛","么","哇",
    # extra stopwords requested
    "这个","足够","大家","很多","事情","什么",
    "时候","这样","的话","一些",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Word frequency for a sender using jieba")
    parser.add_argument("--inputs", nargs="+", required=True, help="Original JSON files")
    parser.add_argument("--sender", required=True, help="Exact senderName to match")
    parser.add_argument("--top", type=int, default=50, help="Top N words to output")
    parser.add_argument("--out", default="", help="Optional output JSON path")
    parser.add_argument("--wordcloud-out", default="", help="Optional output wordcloud PNG")
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


def clean_text(text: str) -> str:
    # Remove URLs and non-text noise; keep Chinese, letters, numbers, and spaces.
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)  # strip simple tags
    text = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", " ", text)
    return text


def main() -> int:
    args = parse_args()
    sender = args.sender

    counter: Counter[str] = Counter()

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
            text = clean_text(content)
            if not text.strip():
                continue
            for token in jieba.lcut(text):
                token = token.strip()
                if not token:
                    continue
                if token in STOPWORDS:
                    continue
                if len(token) == 1:
                    continue
                counter[token] += 1

    top_items = counter.most_common(args.top)

    for word, freq in top_items:
        print(f"{word}\t{freq}")

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(
            json.dumps([{"word": w, "freq": f} for w, f in top_items], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if args.wordcloud_out:
        font_path = r"C:\\Windows\\Fonts\\msyh.ttc"
        wc = WordCloud(
            width=1600,
            height=1000,
            background_color="white",
            font_path=font_path,
            collocations=False,
        ).generate_from_frequencies(counter)
        wc.to_file(args.wordcloud_out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
