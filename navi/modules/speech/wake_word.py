# navi/modules/speech/wake_word.py

import queue
import json
import re
import sounddevice as sd
import vosk

from fuzzywuzzy import fuzz

from navi.modules.speech.tts import play_file, speak
from navi.modules.speech.command_listener import listen_for_command
from navi.modules.ai.ai_brain import ask_openai
from navi.core.paths import model_path, asset_path

WAKE_PHRASES = ["hey navi", "hi navi", "okay navi"]
MODEL_PATH = model_path("vosk-model-small-en-us-0.15")

q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print("[!] Audio status:", status)
    q.put(bytes(indata))

def is_wake_word(text: str) -> bool:
    """Fuzzy + exact matching for robustness."""
    t = (text or "").lower().strip()
    if not t:
        return False
    # exact word-boundary check first (fast path)
    if any(re.search(rf"\b{re.escape(p)}\b", t) for p in WAKE_PHRASES):
        return True
    # fuzzy fallback
    for phrase in WAKE_PHRASES:
        score = fuzz.ratio(phrase, t)
        if score >= 80:
            print(f"[MATCH] '{t}' ≈ '{phrase}' ({score}%)")
            return True
    return False

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
                text = (result.get("text") or "").lower().strip()
                print(f"[DEBUG] Heard: {text}")

                if is_wake_word(text):
                    print("🔊 Wake word detected!")

                    # Play your pre-rendered Olivia chime (under assets/)
                    # Use relative-to-assets path; no leading slash; no '?'
                    play_file("voice_db/Olivia/sir.mp3")

                    # Listen for the command, ask OpenAI, speak response
                    user_command = listen_for_command()
                    print(f"[NÄVÎ] Interpreted command: {user_command or '[empty]'}")

                    if not user_command:
                        speak("I didn't catch that. Please repeat the command.")
                        continue

                    response = ask_openai(user_command)
                    speak(response)
                    return  # Exit so the CLI command completes (or remove to keep looping)
