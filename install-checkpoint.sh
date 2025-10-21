#!/usr/bin/env bash
set -euo pipefail

# download-sdxl.sh — Download requested Civitai checkpoint into ComfyUI
# Usage:
#   ./download-sdxl.sh

MODEL_URL="https://civitai.com/api/download/models/1920523?type=Model&format=SafeTensor&size=pruned&fp=fp16"
MODEL_FILE="epiCRealism-XL"

# ComfyUI path relative to where this script is run
COMFY_DIR="./ComfyUI"
DEST_DIR="${COMFY_DIR}/models/checkpoints"

# Create destination directory if missing
mkdir -p "${DEST_DIR}"

# Temporary download target (mktemp provides a unique file and works on macOS/Linux)
TMP_FILE="$(mktemp)"
cleanup() {
  rm -f "${TMP_FILE}"
}
trap cleanup EXIT

echo "⬇️  Downloading ${MODEL_FILE} from Civitai..."
curl -L --fail -C - -o "${TMP_FILE}" "${MODEL_URL}"

# Verify the file isn’t empty
if [[ ! -s "${TMP_FILE}" ]]; then
  echo "❌ Download failed or file empty."
  exit 2
fi

DEST_PATH="${DEST_DIR}/${MODEL_FILE}"
if [[ -f "${DEST_PATH}" ]]; then
  echo "🟡 Existing model found at ${DEST_PATH}, backing up..."
  mv "${DEST_PATH}" "${DEST_PATH}.bak.$(date +%Y%m%d%H%M%S)"
fi

mv "${TMP_FILE}" "${DEST_PATH}"
trap - EXIT
sync

echo "✅ Checkpoint saved to: ${DEST_PATH}"
echo "You can now open ComfyUI and select it under 'Models → Checkpoints'."
