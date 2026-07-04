import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

print("Hermia Translation Server starting...", flush=True)

LANG_MAP = {
    "fr": "fr", "es": "es", "ar": "ar", "sw": "sw",
    "yo": "yo", "hi": "hi", "de": "de", "pt": "pt",
    "zh": "zh-CN", "ig": "ig", "ha": "ha", "ru": "ru",
    "it": "it", "nl": "nl", "pl": "pl", "uk": "uk",
    "tr": "tr", "vi": "vi", "id": "id",
}

def translate_text(text, target_lang):
    lt_lang = LANG_MAP.get(target_lang, target_lang)

    # Primary: MyMemory free API
    try:
        encoded = urllib.parse.quote(text)
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=en|{lt_lang}"
        req = urllib.request.Request(url, headers={"User-Agent": "Hermia/1.0"})
        with urllib.request.urlopen(req, timeout=8) as response:
            result = json.loads(response.read())
            translated = result["responseData"]["translatedText"]
            status = result["responseStatus"]
            if status == 200 and translated and translated.lower() != text.lower():
                print(f"OK MyMemory [{target_lang}]: {translated[:40]}", flush=True)
                return translated
    except Exception as e:
        print(f"MyMemory failed: {e}", flush=True)

    # Fallback: LibreTranslate
    for server in ["https://translate.argosopentech.com", "https://libretranslate.de"]:
        try:
            payload = json.dumps({"q": text, "source": "en", "target": lt_lang, "format": "text"}).encode()
            req = urllib.request.Request(f"{server}/translate", data=payload,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=8) as response:
                result = json.loads(response.read())
                translated = result.get("translatedText", "")
                if translated and translated.lower() != text.lower():
                    print(f"OK LibreTranslate [{target_lang}]", flush=True)
                    return translated
        except Exception as e:
            print(f"LibreTranslate {server} failed: {e}", flush=True)

    return text

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

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
                "engine": "MyMemory + LibreTranslate fallback",
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
                response = json.dumps({"translated": translated, "source": "en", "target": target_lang}).encode()
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
print(f"Ready on port {PORT} - MyMemory primary, LibreTranslate fallback", flush=True)
HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
