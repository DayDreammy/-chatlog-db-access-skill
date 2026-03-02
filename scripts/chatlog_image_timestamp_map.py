#!/usr/bin/env python
"""Map decoded image filenames to send time/sender info."""
import csv
import json
import os
import sys

if len(sys.argv) < 4:
    print("usage: chatlog_image_timestamp_map.py <json_path> <image_dir> <out_csv>")
    sys.exit(2)

json_path, image_dir, out_csv = sys.argv[1:4]
if not os.path.isfile(json_path):
    raise SystemExit(f"json not found: {json_path}")
if not os.path.isdir(image_dir):
    raise SystemExit(f"image dir not found: {image_dir}")

# collect image stems
img_stems = set()
for name in os.listdir(image_dir):
    if name.lower().endswith('.jpg'):
        img_stems.add(os.path.splitext(name)[0])

with open(json_path, 'r', encoding='utf-8', errors='ignore') as f:
    data = json.load(f)

rows = []
for m in data:
    contents = m.get('contents') or {}
    imgfile = contents.get('imgfile')
    if not imgfile:
        continue
    stem = os.path.splitext(os.path.basename(imgfile))[0]
    if stem in img_stems:
        rows.append({
            'filename': stem + '.jpg',
            'time': m.get('time', ''),
            'sender': m.get('sender', ''),
            'senderName': m.get('senderName', ''),
            'talker': m.get('talker', ''),
        })

with open(out_csv, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['filename','time','sender','senderName','talker'])
    w.writeheader()
    w.writerows(rows)

print("done", len(rows))
