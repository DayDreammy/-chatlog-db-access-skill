# chatlog-db-access skill

Skill package for exporting and processing WeChat chat logs through `chatlog.exe` HTTP API.

## What this repo contains

- `SKILL.md`: skill instructions and workflow
- `references/chatlog-api.md`: API reference notes
- `scripts/`: helper scripts for export, media download/decrypt, markdown/docx conversion, and sender-level analysis

## Quick start

1. Start local chatlog server:

```powershell
chatlog.exe server
```

2. Use the main image export script:

```powershell
python .\scripts\chatlog_export_images.py `
  --talker "wxid_xxx" `
  --start "2025-01-01" `
  --end "2025-12-31" `
  --out-dir "D:\path\exports\talker_export" `
  --ffmpeg "D:\path\ffmpeg.exe" `
  --jpg-dir "D:\path\exports\talker_export\jpg" `
  --delete-bin-after-jpg
```

## Requirements

- Local `chatlog.exe` with decrypted data
- API reachable at `http://127.0.0.1:5030`
- Python 3.x for Python scripts
- PowerShell for `.ps1` scripts
- `ffmpeg` for image/video conversion flows

