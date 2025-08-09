#!/usr/bin/env bash
set -euo pipefail

# -------------------------
# Config (edit these)
# -------------------------
REPO_URL="${REPO_URL:-git@github.com:YOURUSER/YOURREPO.git}"   # or https://...
PROJECT_NAME="${PROJECT_NAME:-navi-watch}"                     # folder name on the Pi
PYTHON_BIN="${PYTHON_BIN:-python3}"                            # python to use
VENV_DIR=".venv"
VOSK_MODEL="vosk-model-small-en-us-0.15"
VOSK_URL="https://alphacephei.com/vosk/models/${VOSK_MODEL}.zip"

# -------------------------
# Derived paths
# -------------------------
HOME_DIR="$(eval echo ~"$SUDO_USER")"
: "${HOME_DIR:=$HOME}"  # fallback if SUDO_USER unset
PROJECT_ROOT="${HOME_DIR}/${PROJECT_NAME}"
MODELS_DIR="${PROJECT_ROOT}/models"
ASSETS_DIR="${PROJECT_ROOT}/assets"

echo "[*] Using HOME_DIR=${HOME_DIR}"
echo "[*] Project root will be ${PROJECT_ROOT}"

# -------------------------
# APT deps (Pi/Ubuntu)
# -------------------------
echo "[*] Updating apt and installing packages…"
sudo apt-get update -y
sudo apt-get install -y \
  git \
  wget unzip curl \
  ${PYTHON_BIN}-venv ${PYTHON_BIN}-dev python3-pip \
  build-essential \
  libportaudio2 portaudio19-dev libsndfile1 \
  alsa-utils \
  mpg123

# -------------------------
# Clone or update repo
# -------------------------
if [[ -d "${PROJECT_ROOT}/.git" ]]; then
  echo "[*] Repo exists. Pulling latest…"
  git -C "${PROJECT_ROOT}" pull --rebase
else
  echo "[*] Cloning repo…"
  git clone "${REPO_URL}" "${PROJECT_ROOT}"
fi

cd "${PROJECT_ROOT}"

# -------------------------
# Python venv
# -------------------------
if [[ ! -d "${VENV_DIR}" ]]; then
  echo "[*] Creating virtual environment…"
  ${PYTHON_BIN} -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip wheel setuptools

# -------------------------
# Requirements
# -------------------------
if [[ -f "requirements.txt" ]]; then
  echo "[*] Installing Python deps from requirements.txt…"
  python -m pip install -r requirements.txt
else
  echo "[!] requirements.txt not found. Installing known-needed deps…"
  python -m pip install \
    boto3 python-dotenv \
    sounddevice vosk \
    fuzzywuzzy python-Levenshtein \
    rich click
fi

# -------------------------
# Models (Vosk)
# -------------------------
mkdir -p "${MODELS_DIR}"
if [[ ! -d "${MODELS_DIR}/${VOSK_MODEL}" ]]; then
  echo "[*] Downloading Vosk model: ${VOSK_MODEL}…"
  tmpzip="$(mktemp /tmp/vosk.XXXXXX.zip)"
  wget -O "${tmpzip}" "${VOSK_URL}"
  unzip -q "${tmpzip}" -d "${MODELS_DIR}"
  rm -f "${tmpzip}"
else
  echo "[*] Vosk model already present."
fi

# -------------------------
# Assets sanity
# -------------------------
mkdir -p "${ASSETS_DIR}/audio" "${ASSETS_DIR}/tts_cache"

echo "[*] Setup complete."
echo "[*] To activate venv next time: source ${PROJECT_ROOT}/${VENV_DIR}/bin/activate"
echo "[*] Try a quick TTS test: python -m navi say \"G'day—Olivia online.\""
