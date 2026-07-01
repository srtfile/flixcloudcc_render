import os
import re
import json
import requests
import json5
from urllib.parse import urlencode
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Referer": "https://flixcloud.cc/"
}
API = "https://enc-dec.app/api"


def validate(data, path):
    if data.get("status") != 200:
        raise ValueError(f"API error at {path}: {data.get('error', 'unknown')} (status {data.get('status')})")
    return data["result"]


def resolve_stream(url):
    logs = []

    # Step 1: Fetch page content
    logs.append({"step": "Fetching page content", "status": "pending"})
    response = requests.get(url, headers=HEADERS, timeout=15).text
    match = re.search(r'type:\s*"data",\s*data:\s*(\{.*?\})\s*,\s*uses:', response, re.S)
    if not match:
        raise ValueError("Could not find embedded data in the page. Make sure the URL is a valid FlixCloud embed.")
    data = json5.loads(match.group(1))
    subtitles = data.pop("subtitles", [])
    logs[-1]["status"] = "done"

    # Step 2: Resolve stream token
    logs.append({"step": "Resolving stream token", "status": "pending"})
    dec_token = f"{API}/dec-flixcloud?type=token"
    token_response = requests.post(dec_token, json={"data": data}, timeout=15).json()
    token_validated = validate(token_response, dec_token)
    logs[-1]["status"] = "done"

    # Step 3: Fetch encrypted stream
    logs.append({"step": "Fetching encrypted stream", "status": "pending"})
    stream_url = f"https://flixcloud.cc/api/m3u8/{token_validated['token']}"
    stream_response = requests.get(stream_url, headers=HEADERS, timeout=15).json()
    logs[-1]["status"] = "done"

    # Step 4: Decrypt stream
    logs.append({"step": "Decrypting stream", "status": "pending"})
    dec_stream = f"{API}/dec-flixcloud?type=stream"
    stream_payload = {
        "data": {
            "context": token_validated["context"],
            "stream_response": stream_response
        }
    }
    stream_dec_response = requests.post(dec_stream, json=stream_payload, timeout=15).json()
    stream_resolved = validate(stream_dec_response, dec_stream)
    logs[-1]["status"] = "done"

    # Step 5: Parse manifest
    logs.append({"step": "Parsing manifest", "status": "pending"})
    params = urlencode({
        "url": stream_resolved["stream"],
        "w_payload": stream_resolved["context"]["w_payload"]
    })
    parse_manifest = f"{API}/parse-flixcloud?{params}"
    manifest_response = requests.get(parse_manifest, timeout=15)
    manifest_text = manifest_response.text
    logs[-1]["status"] = "done"

    return {
        "stream_url": stream_resolved["stream"],
        "manifest": manifest_text,
        "parse_manifest_url": parse_manifest,
        "referer": HEADERS["Referer"],
        "subtitles": subtitles,
        "logs": logs
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/resolve", methods=["POST"])
def resolve():
    body = request.get_json()
    url = (body or {}).get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    if "flixcloud.cc" not in url:
        return jsonify({"error": "Only FlixCloud URLs are supported (e.g. https://flixcloud.cc/e/...)"}), 400
    try:
        result = resolve_stream(url)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. The upstream server may be slow or unavailable."}), 504
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
