import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import urllib.parse

print("Loading NLLB model into memory...", flush=True)

MODEL_NAME = "facebook/nllb-200-distilled-600M"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

print("NLLB ready!", flush=True)

LANG_MAP = {
    "fr": "fra_Latn", "es": "spa_Latn", "ar": "arb_Arab",
    "sw": "swh_Latn", "yo": "yor_Latn", "ha": "hau_Latn",
    "ig": "ibo_Latn", "hi": "hin_Deva", "zh": "zho_Hans",
    "pt": "por_Latn", "de": "deu_Latn", "it": "ita_Latn",
    "ru": "rus_Cyrl", "ja": "jpn_Jpan", "ko": "kor_Hang",
    "uk": "ukr_Cyrl", "tr": "tur_Latn", "vi": "vie_Latn",
    "id": "ind_Latn", "ta": "tam_Taml", "ur": "urd_Arab",
}

def translate(text, target_lang):
    nllb_code = LANG_MAP.get(target_lang, "fra_Latn")
    inputs = tokenizer(text, return_tensors="pt", src_lang="eng_Latn")
    target_id = tokenizer.convert_tokens_to_ids(nllb_code)
    output = model.generate(
        **inputs,
        forced_bos_token_id=target_id,
        max_length=400
    )
    return tokenizer.decode(output[0], skip_special_tokens=True)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress logs

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(length))
        text = body.get("text", "")
        target_lang = body.get("targetLang", "fr")
        translated = translate(text, target_lang)
        response = json.dumps({"translated": translated}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response)

print("Translation server running on port 5000", flush=True)
HTTPServer(("localhost", 5000), Handler).serve_forever()