---
name: chatlog-db-access
description: Access chatlog data through chatlog.exe HTTP API for reading chat logs, contacts, chatrooms, sessions, and media; use when you need to query a time range, filter by talker, export JSON, download/convert images, or map images to send time from a JSON export.
---

# Chatlog DB Access (HTTP API)

## Overview

Use the chatlog.exe HTTP API to read chat logs and media from local data. This skill is API-only (not direct database parsing).

## Workflow Decision Tree

- Need data but server is not running -> start `chatlog.exe server` and verify the API responds.
- Need a talker id (person or group) -> list contacts/chatrooms/sessions, pick the id, then query chat logs.
- Need chat logs for a time range -> call `/api/v1/chatlog` with `time` and `talker`, export JSON.
- Need media (image/video/file/voice) -> fetch via media endpoints, follow redirects if any.
- Need image conversion -> use `scripts/chatlog_media_export.ps1`.
- Need image timestamp mapping -> use `scripts/chatlog_image_timestamp_map.py`.

## Step 1: Start and verify the server

- Default base URL: `http://127.0.0.1:5030`
- Verify the server is running by calling a simple endpoint such as `/api/v1/session`.
- If results are empty, ensure data was decrypted in chatlog.exe before querying.

## Step 2: Resolve the talker id

- People: use `/api/v1/contact`.
- Groups: use `/api/v1/chatroom`.
- Recent conversations: use `/api/v1/session`.

Select the correct talker id (wxid or chatroom id). Use that id in the chatlog query.

### List contacts/chatrooms/sessions (script)

Use `scripts/chatlog_list.ps1` to dump contacts, chatrooms, or sessions to JSON.

Example:

```powershell
.\scripts\chatlog_list.ps1 -Type chatroom -OutFile D:\path\chatrooms.json
```

## Step 3: Query chat logs

Call `/api/v1/chatlog` with:
- `time=YYYY-MM-DD` or `YYYY-MM-DD~YYYY-MM-DD`
- `talker=<talker id>`
- `format=json`
- `limit` and `offset` for pagination

If you need to filter a specific sender inside a group, do it client-side based on the response fields.

## Step 4: Export JSON

Save the response body to a `.json` file. Use PowerShell or curl as needed.

### Export full chat logs for multiple talkers (script)

Use `scripts/chatlog_export_talkers.ps1` to export all chat logs for one or more talkers to JSON arrays, with pagination handled automatically.

Example:

```powershell
.\scripts\chatlog_export_talkers.ps1 `
  -Talkers "1234567890@chatroom","9876543210@chatroom" `
  -OutDir "D:\path\exports" `
  -StartDate "2000-01-01" `
  -EndDate "2026-01-21"
```

### Export all talkers, text-only (script)

Use `scripts/chatlog_export_all_text.ps1` to export text-only messages for all talkers
(contacts + chatrooms + sessions) into per-talker JSON files.

Example:

```powershell
.\scripts\chatlog_export_all_text.ps1 `
  -OutDir "D:\path\exports_text" `
  -StartDate "2000-01-01" `
  -EndDate "2026-01-21"
```

Notes:
- Default text types: `1` (use `-IncludeSystem` to add type `10000`).
- Override types with `-IncludeTypes @(1,10000)` if needed.
- For logging, set `-LogPath "D:\path\exports_text\export_all_text.log"` (also writes to stdout).
- Use `-Resume` to skip talkers that already have an output file.

### Convert simplified JSON to Markdown (script)

Use `scripts/chatlog_export_markdown.py` to convert simplified chatlog JSON into a readable Markdown backup.

Example:

```powershell
python .\scripts\chatlog_export_markdown.py `
  --inputs D:\path\exports\chatlog_simple.json `
           D:\path\exports\chatlog_simple_2.json `
  --out-dir D:\path\exports
```

### Export group images to JPG by time range (script)

Use `scripts/chatlog_export_group_images.ps1` to export all images from a specific chatroom within a time range. The script will fetch chat logs, download images via the HTTP API, and convert them to JPG using ffmpeg.

Example:

```powershell
.\scripts\chatlog_export_group_images.ps1 `
  -Talker "1234567890@chatroom" `
  -StartDate "2025-01-01" `
  -EndDate "2025-12-31" `
  -OutDir "D:\path\group_images" `
  -FfmpegPath "D:\path\ffmpeg.exe"
```


### Export talker images to JPG by time range (script)

Use `scripts/chatlog_export_images.py` to export images for a contact or chatroom within a time range, decrypt via the HTTP API, and convert to JPG using ffmpeg (optional).

Example:

```powershell
python .\scripts\chatlog_export_images.py `
  --talker "wxid_xxx" `
  --start "2025-01-01" `
  --end "2026-01-25" `
  --out-dir "D:\path\exports\talker_export" `
  --ffmpeg "D:\path\ffmpeg.exe" `
  --jpg-dir "D:\path\exports\talker_export\jpg" `
  --delete-bin-after-jpg
```
### Convert Markdown to Word with images (script)

Use `scripts/chatlog_md_to_docx.py` to convert Markdown into Word (docx) and resolve images via `--resource-path`.

Example:

```powershell
python .\scripts\chatlog_md_to_docx.py `
  --md D:\path\chatlog.md `
  --out D:\path\chatlog.docx `
  --resource-path D:\path
```

## Step 5: Fetch media

Use media endpoints to retrieve attachments. Some endpoints return a 302 redirect; follow it.

## Step 6: Export and convert images (script)

Use `scripts/chatlog_media_export.ps1` to download images by `imgfile`/`thumb` from a JSON export, store full images as `.jpg`, and export thumbs as `.jpg`.

Example:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\chatlog_media_export.ps1 `
  -JsonPath "D:\path\chatlog.json" `
  -OutDir "D:\path\media" `
  -BaseUrl "http://127.0.0.1:5030" `
  -FfmpegPath "C:\\path\\to\\ffmpeg.exe"
```

## Step 7: Map images to send time (script)

Use `scripts/chatlog_image_timestamp_map.py` to map decoded image filenames to send time/sender info and output a CSV.

Example:

```bash
python .\scripts\chatlog_image_timestamp_map.py D:\path\chatlog.json D:\path\media D:\path\images.csv
```

## References

- `references/chatlog-api.md`

