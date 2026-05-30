import sys
import json
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

text = sys.argv[1]
target_lang = sys.argv[2]

LANG_MAP = {
    "fr": "fra_Latn", "es": "spa_Latn", "ar": "arb_Arab",
    "sw": "swh_Latn", "yo": "yor_Latn", "ha": "hau_Latn",
    "ig": "ibo_Latn", "hi": "hin_Deva", "zh": "zho_Hans",
    "pt": "por_Latn", "de": "deu_Latn", "it": "ita_Latn",
    "ru": "rus_Cyrl", "ja": "jpn_Jpan", "ko": "kor_Hang",
}

nllb_code = LANG_MAP.get(target_lang, "fra_Latn")

model_name = "facebook/nllb-200-distilled-600M"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

inputs = tokenizer(text, return_tensors="pt", src_lang="eng_Latn")

target_id = tokenizer.convert_tokens_to_ids(nllb_code)

output = model.generate(
    **inputs,
    forced_bos_token_id=target_id,
    max_length=400
)

translated = tokenizer.decode(output[0], skip_special_tokens=True)

print(json.dumps({"translated": translated}))