# navi/modules/speech/command_listener.py

import queue
import sounddevice as sd
import vosk
import json
from pathlib import Path
from navi.core.paths import model_path

MODEL_PATH = model_path("vosk-model-small-en-us-0.15")
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print("[!] Audio status:", status)
    q.put(bytes(indata))

def listen_for_command(duration=5):
    """
    Listens for 'duration' seconds and returns transcribed text.
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Vosk model not found at {MODEL_PATH}")

    print(f"[Command Mode] Listening for command... ({duration}s)")
    model = vosk.Model(str(MODEL_PATH))
    recognizer = vosk.KaldiRecognizer(model, 16000)

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        sd.sleep(duration * 1000)

        full_result = ""
        while not q.empty():
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                full_result += f"{text} "

        # Final flush
        result = json.loads(recognizer.FinalResult())
        final_text = result.get("text", "").strip()
        full_result += f"{final_text}"

    cleaned = full_result.strip()
    print(f"[Command Mode] You said: \"{cleaned}\"")
    return cleaned
