#!/usr/bin/env bash
set -euo pipefail

# install-checkpoint.sh — Download a Civitai checkpoint into ComfyUI.
# Usage:
#   ./install-checkpoint.sh

DEFAULT_MODEL_URL="https://civitai.com/api/download/models/1920523?type=Model&format=SafeTensor&size=pruned&fp=fp16"

read -rp "Enter Civitai checkpoint download URL [${DEFAULT_MODEL_URL}]: " USER_MODEL_URL
MODEL_URL="${USER_MODEL_URL:-$DEFAULT_MODEL_URL}"

if [[ -z "${MODEL_URL}" ]]; then
  echo "❌ A Civitai download URL is required."
  exit 1
fi

detect_filename() {
  local url="$1"
  local header
  header=$(curl -sI -L "$url" | tr -d '\r')
  CURL_HEADER="$header" CURL_URL="$url" python3 - <<'PY'
import os
import sys
import urllib.parse
import re

header = os.environ.get("CURL_HEADER", "")
url = os.environ.get("CURL_URL", "")
filename = ""
for line in header.splitlines():
    if line.lower().startswith("content-disposition:"):
        value = line.split(":", 1)[1]
        match = re.search(r"filename\*=([^;]+)", value, flags=re.I)
        if match:
            candidate = match.group(1)
            if "''" in candidate:
                candidate = candidate.split("''", 1)[1]
            filename = urllib.parse.unquote(candidate.strip('"'))
            break
        match = re.search(r"filename=\"?([^";]+)\"?", value, flags=re.I)
        if match:
            filename = match.group(1)
            break
if not filename:
    parsed = urllib.parse.urlparse(url)
    filename = os.path.basename(parsed.path.rstrip('/'))
if not filename:
    filename = "model.safetensors"
print(filename)
PY
}

MODEL_FILE="$(detect_filename "${MODEL_URL}")"

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
