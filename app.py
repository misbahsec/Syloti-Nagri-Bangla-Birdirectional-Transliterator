# app.py
# Flask backend for the Bengali <-> Syloti Nagri transliterator.
# Every asset lives in this same folder: no static/ or templates/ subfolders.

import os
import time

from flask import Flask, jsonify, request, send_from_directory

import sylphonetic
from transliterator import SUPPORTED_DIRECTIONS, transliterate

# Absolute path of the folder containing this file. Using an absolute path makes
# send_from_directory work no matter what the process working directory is.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Reject absurdly large payloads before they reach the transliterator.
MAX_INPUT_CHARS = 20_000

# How the input text is written.
#   bangla   : Bangla script, sent straight to the engine (the original behaviour)
#   phonetic : Sylheti typed in English letters. It is first rebuilt in Bangla
#              script by sylphonetic.py, and that Bangla goes to the engine.
#   auto     : detected per request. Any English letters (outside URLs, numbers
#              and {escapes}) go through the phonetic step; Bangla-script parts
#              pass through untouched, so code-mixed text works. The web page
#              always sends auto.
INPUT_MODES = ("auto", "bangla", "phonetic")

# Roman -> Bangla lexicon. Loaded once per worker. Drop a lexicon.json next to
# this file (python sylphonetic.py build corpus.txt lexicon.json) to extend it.
PHONETIC_LEXICON, PHONETIC_SOURCE = sylphonetic.load_app_lexicon(BASE_DIR)

app = Flask(__name__)
START_TIME = time.time()


# --------------------------------------------------------------------------- #
# CORS
# --------------------------------------------------------------------------- #
@app.after_request
def add_cors_headers(response):
    """Allow cross-origin use of the API (e.g. from a separate front end)."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Max-Age"] = "86400"
    return response


# --------------------------------------------------------------------------- #
# Static files (served from the project root, not a static/ folder)
# --------------------------------------------------------------------------- #
@app.route("/")
def home():
    """Serve index.html from the current directory."""
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/style.css")
def serve_css():
    """Serve style.css from the current directory with the correct MIME type."""
    return send_from_directory(BASE_DIR, "style.css", mimetype="text/css")


@app.route("/favicon.ico")
def favicon():
    """No favicon file exists; answer 204 instead of logging a 404 on every load."""
    return ("", 204)


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
@app.route("/health", methods=["GET"])
def health():
    """Lightweight status probe. Runs one real conversion to prove the engine works."""
    try:
        probe = transliterate("অ", "bn_to_syl")
        engine_ok = bool(probe)
    except Exception:
        engine_ok = False

    payload = {
        "status": "ok" if engine_ok else "degraded",
        "engine": "SylhetiTransliterator",
        "directions": list(SUPPORTED_DIRECTIONS),
        "input_modes": list(INPUT_MODES),
        "phonetic": {
            "lexicon_source": PHONETIC_SOURCE,
            "lexicon_keys": len(PHONETIC_LEXICON),
        },
        "uptime_seconds": round(time.time() - START_TIME, 1),
    }
    return jsonify(payload), (200 if engine_ok else 503)


@app.route("/transliterate", methods=["GET", "POST", "OPTIONS"])
def transliterate_route():
    """
    Convert text between Bengali and Syloti Nagri.

    GET   /transliterate?text=...&direction=bn_to_syl&input_mode=phonetic
    POST  /transliterate   {"text": "...", "direction": "bn_to_syl",
                            "input_mode": "phonetic"}

    input_mode is optional: "auto", "bangla" or "phonetic". It defaults to
    "bangla", so existing API clients behave exactly as before. The original
    response fields are unchanged:
        {"input": ..., "output": ..., "direction": ...}
    For bn_to_syl with "auto" or "phonetic" these are added:
        "input_mode": as sent,
        "detected":   "bangla" | "phonetic" | "mixed"
    and, whenever the phonetic step ran:
        "bangla":     the Bangla-script text that was actually converted,
        "guesses":    Roman words not found in the lexicon (rule-based guesses)
    """
    # Browsers send a preflight before cross-origin JSON POSTs.
    if request.method == "OPTIONS":
        return ("", 204)

    if request.method == "GET":
        text = request.args.get("text", "")
        direction = request.args.get("direction", "bn_to_syl")
        input_mode = request.args.get("input_mode", "bangla")
    else:
        # silent=True so a wrong/missing Content-Type returns our JSON error
        # instead of Flask's default HTML 400 page.
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"error": "Invalid JSON payload"}), 400
        if not isinstance(data, dict):
            return jsonify({"error": "JSON body must be an object"}), 400
        text = data.get("text", "")
        direction = data.get("direction", "bn_to_syl")
        input_mode = data.get("input_mode", "bangla")

    if not isinstance(text, str):
        return jsonify({"error": "Field 'text' must be a string"}), 400

    if not text.strip():
        return jsonify({"error": "No text provided"}), 400

    if len(text) > MAX_INPUT_CHARS:
        return (
            jsonify(
                {
                    "error": f"Text too long. Limit is {MAX_INPUT_CHARS} characters.",
                    "limit": MAX_INPUT_CHARS,
                    "received": len(text),
                }
            ),
            413,
        )

    if direction not in SUPPORTED_DIRECTIONS:
        return (
            jsonify(
                {
                    "error": 'Direction must be "bn_to_syl" or "syl_to_bn"',
                    "received": direction,
                }
            ),
            400,
        )

    if input_mode not in INPUT_MODES:
        return (
            jsonify(
                {
                    "error": 'input_mode must be "auto", "bangla" or "phonetic"',
                    "received": input_mode,
                }
            ),
            400,
        )

    if input_mode == "phonetic" and direction != "bn_to_syl":
        return (
            jsonify({"error": 'Phonetic input only works with direction "bn_to_syl"'}),
            400,
        )

    # Decide whether the phonetic step runs.
    detected = None
    if direction == "bn_to_syl" and input_mode in ("auto", "phonetic"):
        detected = sylphonetic.detect(text)
    run_phonetic = input_mode == "phonetic" or (
        input_mode == "auto" and detected in ("phonetic", "mixed")
    )

    bangla, guesses = text, []
    if run_phonetic:
        try:
            bangla, guesses = sylphonetic.parse(
                text, PHONETIC_LEXICON, mark_guesses=True
            )
        except Exception as exc:  # noqa: BLE001
            app.logger.exception("Phonetic parsing failed")
            return jsonify({"error": f"Phonetic parsing failed: {exc}"}), 500

    try:
        result = transliterate(bangla, direction)
    except Exception as exc:  # noqa: BLE001 - surface engine faults as 500 JSON
        app.logger.exception("Transliteration failed")
        return jsonify({"error": f"Transliteration failed: {exc}"}), 500

    payload = {"input": text, "output": result, "direction": direction}
    if detected is not None:
        payload.update({"input_mode": input_mode, "detected": detected})
    if run_phonetic:
        payload.update(
            {
                "bangla": bangla,
                # De-duplicated, first-seen order
                "guesses": list(dict.fromkeys(guesses)),
            }
        )
    return jsonify(payload)


# --------------------------------------------------------------------------- #
# Error handlers: keep every response JSON so the front end can always parse it
# --------------------------------------------------------------------------- #
@app.errorhandler(404)
def handle_404(_error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(405)
def handle_405(_error):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def handle_500(_error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)