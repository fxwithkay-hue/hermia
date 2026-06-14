import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

print("Hermia Translation Server starting...", flush=True)

# Language code mapping — our codes to LibreTranslate codes
LANG_MAP = {
    "fr": "fr",
    "es": "es",
    "ar": "ar",
    "sw": "sw",
    "yo": "yo",
    "hi": "hi",
    "de": "de",
    "pt": "pt",
    "zh": "zh",
    "ig": "ig",
    "ha": "ha",
    "ru": "ru",
    "it": "it",
    "nl": "nl",
    "pl": "pl",
    "uk": "uk",
    "tr": "tr",
    "vi": "vi",
    "id": "id",
}

# Free LibreTranslate instances (public, no key needed)
LIBRE_SERVERS = [
    "https://libretranslate.com",
    "https://translate.argosopentech.com",
    "https://libretranslate.de",
]

def translate_text(text, target_lang):
    """Try multiple free LibreTranslate servers."""
    lt_lang = LANG_MAP.get(target_lang, target_lang)

    for server in LIBRE_SERVERS:
        try:
            payload = json.dumps({
                "q": text,
                "source": "en",
                "target": lt_lang,
                "format": "text"
            }).encode()

            req = urllib.request.Request(
                f"{server}/translate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=8) as response:
                result = json.loads(response.read())
                translated = result.get("translatedText", text)
                print(f"✓ Translated to {target_lang} via {server}", flush=True)
                return translated

        except Exception as e:
            print(f"✗ {server} failed: {e}", flush=True)
            continue

    # All servers failed — return original text
    print(f"⚠ All translation servers failed for {target_lang}", flush=True)
    return text


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default logs

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({
                "status": "Hermia Translation Server running",
                "engine": "LibreTranslate",
                "supported_languages": list(LANG_MAP.keys())
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            text = body.get("text", "")
            target_lang = body.get("targetLang", "fr")

            if not text:
                response = json.dumps({"error": "No text provided"}).encode()
                self.send_response(400)
            else:
                translated = translate_text(text, target_lang)
                response = json.dumps({
                    "translated": translated,
                    "source": "en",
                    "target": target_lang
                }).encode()
                self.send_response(200)

            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", len(response))
            self.end_headers()
            self.wfile.write(response)

        except Exception as e:
            print(f"Error: {e}", flush=True)
            error = json.dumps({"error": str(e)}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(error))
            self.end_headers()
            self.wfile.write(error)


PORT = int(os.environ.get("PORT", 5000))
print(f"✓ Translation server ready on port {PORT}", flush=True)
print(f"✓ Using LibreTranslate — no heavy models needed", flush=True)
HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
