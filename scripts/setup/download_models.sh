#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MODELS_DIR="$REPO_ROOT/brain/voice/models"
mkdir -p "$MODELS_DIR"

VOSK_MODEL_DIR="$MODELS_DIR/vosk-model-small-en-us"
VOSK_URL="https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"

if [[ -d "$VOSK_MODEL_DIR" ]]; then
    echo "[Vosk] Model already exists at $VOSK_MODEL_DIR — skipping download."
else
    echo "[Vosk] Downloading small English model (~40 MB)..."
    wget -q --show-progress -O "$MODELS_DIR/vosk-model.zip" "$VOSK_URL"
    echo "[Vosk] Extracting..."
    unzip -q "$MODELS_DIR/vosk-model.zip" -d "$MODELS_DIR/"
    rm "$MODELS_DIR/vosk-model.zip"
    echo "[Vosk] Model ready at $VOSK_MODEL_DIR"
fi

PIPER_DIR="$MODELS_DIR/piper"
mkdir -p "$PIPER_DIR"

PIPER_ONNX="$PIPER_DIR/en_US-lessac-medium.onnx"
PIPER_JSON="$PIPER_DIR/en_US-lessac-medium.onnx.json"

if [[ -f "$PIPER_ONNX" ]]; then
    echo "[Piper] Model already exists — skipping download."
else
    echo "[Piper] Downloading en_US-lessac-medium voice model..."
    BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
    wget -q --show-progress -O "$PIPER_ONNX" "$BASE_URL/en_US-lessac-medium.onnx"
    wget -q --show-progress -O "$PIPER_JSON" "$BASE_URL/en_US-lessac-medium.onnx.json"
    echo "[Piper] Model ready at $PIPER_DIR"
fi

echo ""
echo "=== Models downloaded ==="
echo "  Vosk: $VOSK_MODEL_DIR"
echo "  Piper: $PIPER_DIR"
echo ""
echo "Update config/brain.yaml:"
echo "  voice.vosk_model_path: $VOSK_MODEL_DIR"
echo "  audio.piper_model_path: $PIPER_ONNX"
