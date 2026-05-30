import sys
import json
import time
from faster_whisper import WhisperModel

audio_path = sys.argv[1]
language = sys.argv[2] if len(sys.argv) > 2 else None

model = WhisperModel("base", device="cpu", compute_type="int8")

start = time.time()
segments, info = model.transcribe(audio_path, language=language)
latency = round(time.time() - start, 2)

text = " ".join([seg.text for seg in segments]).strip()

print(json.dumps({
    "text": text,
    "language": info.language,
    "latency": latency
}))