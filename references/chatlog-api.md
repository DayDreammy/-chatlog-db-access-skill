# Chatlog HTTP API Reference (chatlog.exe server)

## Base URL

- `http://127.0.0.1:5030`

## Core endpoints

- `GET /api/v1/chatlog`
  - Params:
    - `time`: `YYYY-MM-DD` or `YYYY-MM-DD~YYYY-MM-DD`
    - `talker`: wxid, chatroom id, remark name, or nickname
    - `limit`: number of records
    - `offset`: pagination offset
    - `format`: `json` or `csv`

- `GET /api/v1/contact` (list contacts)
- `GET /api/v1/chatroom` (list chatrooms)
- `GET /api/v1/session` (list recent sessions)

## Media endpoints

- `GET /image/<id>`
- `GET /video/<id>`
- `GET /file/<id>`
- `GET /voice/<id>`
- `GET /data/<data dir relative path>`

Notes:
- Media endpoints may return a 302 redirect to the actual media URL.
- Voice content is returned as audio (the server converts to MP3).
- Encrypted images are decrypted by the server on request.

## Example requests (PowerShell)

```powershell
# Chat logs for a time range, JSON
Invoke-WebRequest -Uri "http://127.0.0.1:5030/api/v1/chatlog?time=2024-01-01~2024-01-31&talker=wxid_xxx&format=json" -OutFile .\chatlog.json

# List chatrooms
Invoke-WebRequest -Uri "http://127.0.0.1:5030/api/v1/chatroom" -OutFile .\chatrooms.json

# Fetch an image (follow redirect)
Invoke-WebRequest -MaximumRedirection 5 -Uri "http://127.0.0.1:5030/image/<id>" -OutFile .\image.bin
```

## Example requests (curl)

```bash
# Chat logs for a time range, JSON
curl "http://127.0.0.1:5030/api/v1/chatlog?time=2024-01-01~2024-01-31&talker=wxid_xxx&format=json" -o chatlog.json

# Fetch an image (follow redirect)
curl -L "http://127.0.0.1:5030/image/<id>" -o image.bin
```
