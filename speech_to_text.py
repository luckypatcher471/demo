import sounddevice as sd
import vosk
import queue
import sys
import json
import threading
from pathlib import Path

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR = get_base_dir()

MODEL_PATH = BASE_DIR / "vosk-model-small-en-us-0.15" / "vosk-model-small-en-us-0.15_c_" / "vosk-model-small-en-us-0.15"

if not MODEL_PATH.exists():
    # Fallback to a safer check or raise error
    raise FileNotFoundError(f"Vosk model not found at {MODEL_PATH}")

model = vosk.Model(str(MODEL_PATH))

q = queue.Queue()
stop_listening_flag = threading.Event()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def record_voice(prompt="🎙 I'm listening, sir...", ui=None):
    """
    Blocking call, returns the first recognized sentence.
    """
    print(prompt)
    if ui:
        ui.update_transcript("Listening...")

    rec = vosk.KaldiRecognizer(model, 16000)
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        while not stop_listening_flag.is_set():
            try:
                data = q.get(timeout=0.1)
            except queue.Empty:
                continue
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if text.strip():
                    print("👤 You:", text)
                    if ui:
                        ui.update_transcript(text)
                    return text
            else:
                # Partial result for real-time feel
                partial = json.loads(rec.PartialResult())
                p_text = partial.get("partial", "")
                if p_text.strip() and ui:
                    ui.update_transcript(p_text)

    return ""
