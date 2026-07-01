# FlixCloud Stream Resolver

A web app that decrypts and extracts HLS stream URLs from FlixCloud embeds. Compatible with sites like reanime.to, 1anime.app, and others using FlixCloud.

## Deploy to Render (Free)

### Option 1 — One-click via render.yaml
1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → **New** → **Web Service**
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — just click **Deploy**

### Option 2 — Manual setup on Render
1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → **New** → **Web Service**
3. Connect your GitHub repo and fill in:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60`
   - **Python Version:** 3.11
4. Click **Create Web Service**

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000

## Usage

Paste any FlixCloud embed URL (e.g. `https://flixcloud.cc/e/olygrhle7ty7?v=2`) into the input box and click **Resolve**. The app will:

1. Fetch the embed page
2. Resolve the stream token
3. Fetch the encrypted stream
4. Decrypt the stream
5. Parse and return the M3U8 manifest

Feed the resulting stream URL + `Referer: https://flixcloud.cc/` header to any HLS player (VLC, mpv, etc).

## Project Structure

```
flixcloud-app/
├── app.py           # Flask backend
├── templates/
│   └── index.html   # Frontend UI
├── requirements.txt
├── render.yaml      # Render deployment config
└── README.md
```
