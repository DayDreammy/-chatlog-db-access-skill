import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
import subprocess

DEFAULT_BASE_URL = 'http://127.0.0.1:5030'


def parse_args():
    p = argparse.ArgumentParser(
        description='Export chatlog JSON and image media for a talker, decrypt images, and convert to JPG.'
    )
    p.add_argument('--talker', required=True, help='Talker id, e.g. wxid_xxx or 123@chatroom')
    p.add_argument('--start', required=True, help='Start date YYYY-MM-DD')
    p.add_argument('--end', required=True, help='End date YYYY-MM-DD')
    p.add_argument('--out-dir', required=True, help='Output directory')
    p.add_argument('--base-url', default=DEFAULT_BASE_URL, help='Chatlog API base URL')
    p.add_argument('--ffmpeg', default='', help='Path to ffmpeg.exe (optional for JPG conversion)')
    p.add_argument('--jpg-dir', default='', help='Directory for converted JPGs (default: images dir)')
    p.add_argument('--delete-bin-after-jpg', action='store_true',
                   help='Delete original non-JPG file after successful JPG conversion')
    p.add_argument('--limit', type=int, default=1000, help='Page size for chatlog API')
    return p.parse_args()


def safe_json_loads(data_bytes):
    try:
        return json.loads(data_bytes.decode('utf-8'))
    except Exception:
        text = data_bytes.decode('utf-8', errors='ignore')
        if not text.strip():
            return []
        return json.loads(text)


def http_get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'chatlog-export-script'})
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def export_chatlog(base_url, talker, start, end, limit):
    all_msgs = []
    offset = 0
    while True:
        q = f'{base_url}/api/v1/chatlog?time={start}~{end}&talker={urllib.parse.quote(talker)}&format=json&limit={limit}&offset={offset}'
        data = safe_json_loads(http_get(q))
        if not isinstance(data, list) or not data:
            break
        all_msgs.extend(data)
        if len(data) < limit:
            break
        offset += limit
    return all_msgs


def detect_ext(buf):
    if buf.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if buf.startswith(b'\x89PNG'):
        return 'png'
    if buf.startswith(b'GIF87a') or buf.startswith(b'GIF89a'):
        return 'gif'
    if buf.startswith(b'BM'):
        return 'bmp'
    if buf[:4] == b'RIFF' and buf[8:12] == b'WEBP':
        return 'webp'
    if b'ftyp' in buf[:16]:
        # HEIF/HEIC containers (e.g. ftypheic, ftypmif1, ftypcmfc)
        return 'heic'
    return 'bin'


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def save_file(path, data):
    with open(path, 'wb') as f:
        f.write(data)


def fetch_media(base_url, rel_path):
    rel = rel_path.replace('\\', '/')
    url = f'{base_url}/data/{urllib.parse.quote(rel, safe="/")}'
    req = urllib.request.Request(url, headers={'User-Agent': 'chatlog-export-script'})
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def convert_to_jpg(ffmpeg, src, dst):
    if not ffmpeg:
        return False
    cmd = [ffmpeg, '-y', '-loglevel', 'error', '-i', src, '-frames:v', '1', dst]
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 0


def main():
    args = parse_args()
    ensure_dir(args.out_dir)

    images_dir = os.path.join(args.out_dir, 'images')
    ensure_dir(images_dir)
    jpg_dir = args.jpg_dir if args.jpg_dir else images_dir
    ensure_dir(jpg_dir)

    msgs = export_chatlog(args.base_url, args.talker, args.start, args.end, args.limit)

    json_path = os.path.join(args.out_dir, f'{args.talker}-{args.start}-to-{args.end}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(msgs, f, ensure_ascii=False)

    images = []
    for m in msgs:
        if m.get('type') != 3:
            continue
        contents = m.get('contents') or {}
        imgfile = contents.get('imgfile')
        thumb = contents.get('thumb')
        md5 = contents.get('md5') or ''
        images.append((m, imgfile, thumb, md5))

    saved = 0
    converted = 0
    rows = []

    for m, imgfile, thumb, md5 in images:
        chosen = imgfile or thumb
        if not chosen:
            continue

        data = b''
        try:
            data = fetch_media(args.base_url, chosen)
        except Exception:
            if imgfile and thumb:
                try:
                    data = fetch_media(args.base_url, thumb)
                except Exception:
                    data = b''
        if not data:
            continue

        ext = detect_ext(data[:16])
        name = md5 if md5 else os.path.splitext(os.path.basename(chosen))[0]
        filename = f'{name}.{ext}'
        out_path = os.path.join(images_dir, filename)
        if not os.path.exists(out_path):
            save_file(out_path, data)

        saved += 1

        # convert if needed
        if ext != 'jpg' and args.ffmpeg:
            jpg_path = os.path.join(jpg_dir, f'{name}.jpg')
            if not os.path.exists(jpg_path):
                if convert_to_jpg(args.ffmpeg, out_path, jpg_path):
                    converted += 1
                    if args.delete_bin_after_jpg:
                        try:
                            os.remove(out_path)
                        except Exception:
                            pass

        rows.append({
            'filename': filename,
            'time': m.get('time', ''),
            'sender': m.get('sender', ''),
            'senderName': m.get('senderName', ''),
            'talker': m.get('talker', ''),
        })

    csv_path = os.path.join(args.out_dir, f'{args.talker}-{args.start}-to-{args.end}-images.csv')
    with open(csv_path, 'w', encoding='utf-8-sig') as f:
        f.write('filename,time,sender,senderName,talker\n')
        for r in rows:
            f.write(f"{r['filename']},{r['time']},{r['sender']},{r['senderName']},{r['talker']}\n")

    print(f'messages: {len(msgs)}')
    print(f'image messages: {len(images)}')
    print(f'images saved: {saved}')
    print(f'jpg converted: {converted}')
    print(f'json: {json_path}')
    print(f'csv: {csv_path}')
    print(f'images dir: {images_dir}')
    if jpg_dir != images_dir:
        print(f'jpg dir: {jpg_dir}')


if __name__ == '__main__':
    main()
