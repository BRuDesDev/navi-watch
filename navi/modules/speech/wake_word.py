# navi/modules/speech/wake_word.py

import queue
import sounddevice as sd
import vosk
import json
import re
from pathlib import Path

WAKE_PHRASES = ["hey navi", "hi navi", "okay navi"]

MODEL_PATH = Path("models/vosk-model-small-en-us-0.15")

q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print("[!] Audio status:", status)
    q.put(bytes(indata))


def listen_for_wake_word():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Vosk model not found at {MODEL_PATH}")


    model = vosk.Model(str(MODEL_PATH))
    recognizer = vosk.KaldiRecognizer(model, 16000)

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("[NÄVÎ] Listening for wake word...")

        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()
                print(f"[DEBUG] Heard: {text}")
                if any(re.search(rf"\b{phrase}\b", text) for phrase in WAKE_PHRASES):
                    print("🔊 Wake word detected!")
                    return  # Exit so main program can take over

