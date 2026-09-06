# Syltrans

Syltrans is a bidirectional transliterator between Bengali (Bangla) and Syloti Nagri script. It provides a browser interface and a small Flask JSON API.

## Features

- Bengali to Syloti Nagri conversion
- Syloti Nagri to Bengali conversion
- Automatic conversion while typing
- Light and dark themes
- Copy and swap controls
- JSON API with a health endpoint

## Run Locally

Requires Python 3.10 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open <http://localhost:5000> in a browser.

For a production-style local run:

```powershell
gunicorn app:app
```

## API

Health check:

```http
GET /health
```

Convert text:

```http
POST /transliterate
Content-Type: application/json

{
  "text": "বাংলা",
  "direction": "bn_to_syl"
}
```

Supported directions are `bn_to_syl` and `syl_to_bn`.

The response has this shape:

```json
{
  "input": "বাংলা",
  "output": "...",
  "direction": "bn_to_syl"
}
```

A GET request is also supported:

```text
/transliterate?text=বাংলা&direction=bn_to_syl
```

## Deploy on Render

Create a Render **Web Service** connected to this GitHub repository with:

- Environment: `Python 3`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Health check path: `/health`

The app serves `index.html` and `style.css` from the project root. Render provides the public `onrender.com` URL after the service finishes deploying.

## Project Layout

- `app.py` - Flask server and API routes
- `transliterator.py` - Bengali and Syloti Nagri conversion engine
- `index.html` - web interface
- `style.css` - interface styles
- `requirements.txt` - Python dependencies
- `.github/skills/render-deploy/SKILL.md` - repeatable GitHub-to-Render deployment workflow
