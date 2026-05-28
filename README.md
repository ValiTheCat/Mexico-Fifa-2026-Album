# FIFA 2026 Sticker Tracker ⚽

A personal Panini sticker tracker for the FIFA World Cup 2026 album.

## Features
- All 48 teams, 980 stickers
- Color-coded rarity borders (base / blue / purple / red / foil)
- Wikipedia player photos
- Google Sheets as persistent database
- Works on any device via browser

## Setup

### 1. Google Sheets
- Create a Google Sheet named exactly: `fifa2026_tracker`
- Share it with your service account email (Editor access)

### 2. Streamlit Secrets
In your Streamlit app settings → Secrets, paste:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

### 3. Deploy
- Branch: `main`
- Main file path: `app.py`

## Usage
- Click any sticker's **Open** button to see player photo + details
- Toggle owned/missing
- Set rarity with the dropdown (base → blue → purple → red → foil)
- All changes save instantly to Google Sheets
