import os
import hashlib
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from navi.core.paths import asset_path  # NEW

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

POLLY_VOICE  = os.getenv("POLLY_VOICE", "Olivia")
POLLY_ENGINE = os.getenv("POLLY_ENGINE", "neural")
POLLY_REGION = os.getenv("AWS_REGION", "us-east-1")
POLLY_LANG   = os.getenv("POLLY_LANG", "en-AU")

# Cache lives in assets/tts_cache
CACHE_DIR = asset_path("tts_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_polly = boto3.client("polly", region_name=POLLY_REGION)

def _cache_key(text: str, voice: str, engine: str, lang: str) -> Path:
    h = hashlib.sha256(f"{voice}|{engine}|{lang}|{text}".encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{h}.mp3"

def _synthesize_to_mp3(text: str, out_path: Path, voice: str, engine: str, lang: str):
    kwargs = {"Text": text, "VoiceId": voice, "OutputFormat": "mp3", "Engine": engine, "LanguageCode": lang}
    if text.strip().startswith("<speak"):
        kwargs["TextType"] = "ssml"
    try:
        resp = _polly.synthesize_speech(**kwargs)
        audio = resp.get("AudioStream")
        if not audio:
            raise RuntimeError("Polly returned no AudioStream.")
        with open(out_path, "wb") as f:
            f.write(audio.read())
    except (BotoCoreError, ClientError) as e:
        if engine.lower() == "neural":
            resp = _polly.synthesize_speech(Text=text, VoiceId=voice, OutputFormat="mp3",
                                            Engine="standard", LanguageCode=lang)
            audio = resp.get("AudioStream")
            if not audio:
                raise RuntimeError("Polly returned no AudioStream (fallback).")
            with open(out_path, "wb") as f:
                f.write(audio.read())
            print("[TTS] Fallback to standard engine.")
        else:
            raise

def _play_mp3(path: Path):
    os.system(f'mpg123 "{path}"')

def speak(text: str, voice: str = POLLY_VOICE, engine: str = POLLY_ENGINE, lang: str = POLLY_LANG):
    if not text or not text.strip():
        text = "I'm sorry, I didn't catch that."
    print(f"[TTS] Polly voice={voice} engine={engine} lang={lang}")
    out_path = _cache_key(text, voice, engine, lang)
    if not out_path.exists():
        print("[TTS] Cache miss → synthesizing…")
        _synthesize_to_mp3(text, out_path, voice, engine, lang)
    else:
        print("[TTS] Cache hit → reusing mp3")
    _play_mp3(out_path)

def play_file(filepath: str | Path):
    p = filepath if isinstance(filepath, Path) else asset_path(filepath) if isinstance(filepath, str) else None
    if p is None:
        print("[TTS] Invalid filepath.")
        return
    p = Path(p).resolve()
    if not p.exists():
        print(f"[TTS] Audio file not found: {p}")
        return
    print(f"[TTS] Playing file: {p}")
    _play_mp3(p)
