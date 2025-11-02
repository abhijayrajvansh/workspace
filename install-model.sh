#!/usr/bin/env bash
set -euo pipefail

# install-checkpoint.sh — Simple script to download models into ComfyUI
# Usage: ./install-checkpoint.sh

echo "🤖 ComfyUI Model Installer"
echo "=========================="

# Get model URL
read -rp "Enter model download URL: " MODEL_URL
if [[ -z "${MODEL_URL}" ]]; then
  echo "❌ Model URL is required."
  exit 1
fi

# Detect provider from URL and gather access tokens when needed
MODEL_HOST="${MODEL_URL#*://}"
MODEL_HOST="${MODEL_HOST%%/*}"
if [[ -z "${MODEL_HOST}" ]]; then
  MODEL_HOST="unknown"
fi

DISPLAY_HOST="${MODEL_HOST}"
MODEL_HOST_LOWER=$(printf '%s\n' "${MODEL_HOST}" | tr '[:upper:]' '[:lower:]')

echo "🌐 Download host detected: ${DISPLAY_HOST}"

ACCESS_PROVIDER="Unknown"
AUTH_HEADERS=()

case "${MODEL_HOST_LOWER}" in
  *civitai.com)
    ACCESS_PROVIDER="Civitai"
    echo ""
    echo "🔑 Detected Civitai download. Some files require an API token."
    read -rp "Enter your Civitai API token (optional, press Enter to skip): " CIVITAI_TOKEN
    if [[ -n "${CIVITAI_TOKEN}" ]]; then
      echo "Using Civitai token: ${CIVITAI_TOKEN}"
      AUTH_HEADERS+=(-H "Authorization: Bearer ${CIVITAI_TOKEN}")
    else
      echo "No Civitai token provided."
    fi
    echo "💡 Tip: Generate a token at https://civitai.com/user/account"
    ;;
  *huggingface.co)
    ACCESS_PROVIDER="Hugging Face"
    echo ""
    echo "🔑 Detected Hugging Face download. Private repositories need an access token."
    read -rp "Enter your Hugging Face token (optional, press Enter to skip): " HF_TOKEN
    if [[ -n "${HF_TOKEN}" ]]; then
      echo "Using Hugging Face token: ${HF_TOKEN}"
      AUTH_HEADERS+=(-H "Authorization: Bearer ${HF_TOKEN}")
    else
      echo "No Hugging Face token provided."
    fi
    echo "💡 Tip: Create tokens at https://huggingface.co/settings/tokens"
    ;;
  *)
    echo ""
    echo "ℹ️  No provider-specific authentication detected."
    ;;
esac

# Choose destination directory
echo ""
echo "ℹ️  Common ComfyUI directories:"
DEST_OPTIONS=(
  "ComfyUI/models/checkpoints"
  "ComfyUI/models/loras"
  "ComfyUI/models/vae"
  "ComfyUI/models/facerestore_models"
  "ComfyUI/models/insightface"
  "ComfyUI/models/ultralytics/bbox"
  "ComfyUI/models/vfi"
)

for idx in "${!DEST_OPTIONS[@]}"; do
  printf '   %d) %s\n' "$((idx + 1))" "${DEST_OPTIONS[idx]}"
done

CUSTOM_CHOICE=$(( ${#DEST_OPTIONS[@]} + 1 ))
printf '   %d) Enter a custom directory\n' "${CUSTOM_CHOICE}"

read -rp "Select destination (1-${CUSTOM_CHOICE}): " DEST_CHOICE
if [[ -z "${DEST_CHOICE}" ]]; then
  echo "❌ Destination choice is required."
  exit 1
fi

if ! [[ "${DEST_CHOICE}" =~ ^[0-9]+$ ]]; then
  echo "❌ Destination choice must be a number."
  exit 1
fi

if (( DEST_CHOICE >= 1 && DEST_CHOICE <= ${#DEST_OPTIONS[@]} )); then
  DEST_DIR="./${DEST_OPTIONS[DEST_CHOICE-1]}"
else
  if (( DEST_CHOICE == CUSTOM_CHOICE )); then
    read -rp "Enter destination directory: " CUSTOM_DIR
    if [[ -z "${CUSTOM_DIR}" ]]; then
      echo "❌ Custom directory cannot be empty."
      exit 1
    fi
    DEST_DIR="${CUSTOM_DIR}"
  else
    echo "❌ Invalid destination selection."
    exit 1
  fi
fi

MODEL_TYPE="$(basename "${DEST_DIR}")"

# Create destination directory
mkdir -p "${DEST_DIR}"

# Helper to sanitize filenames (removes invalid characters, trims whitespace)
sanitize_filename() {
  local filename="$1"
  filename=$(echo "${filename}" | sed 's/[<>:"/\\|?*]//g')
  filename=$(echo "${filename}" | sed 's/^[[:space:].]*//' | sed 's/[[:space:]]*$//')
  echo "${filename}"
}

# Suggest an output filename based on the URL
URL_CLEAN="${MODEL_URL%%#*}"
URL_CLEAN="${URL_CLEAN%%\?*}"
URL_CLEAN="${URL_CLEAN%/}"
URL_BASENAME="${URL_CLEAN##*/}"
DEFAULT_FILENAME=$(sanitize_filename "${URL_BASENAME}")

echo ""
if [[ -n "${DEFAULT_FILENAME}" ]]; then
  read -rp "Enter output filename with extension [${DEFAULT_FILENAME}]: " USER_FILENAME
  if [[ -z "${USER_FILENAME}" ]]; then
    USER_FILENAME="${DEFAULT_FILENAME}"
  fi
else
  read -rp "Enter output filename with extension: " USER_FILENAME
  if [[ -z "${USER_FILENAME}" ]]; then
    echo "❌ Filename is required."
    exit 1
  fi
fi

CLEAN_FILENAME=$(sanitize_filename "${USER_FILENAME}")
if [[ -z "${CLEAN_FILENAME}" ]]; then
  echo "❌ Invalid filename. Please use only valid characters."
  exit 1
fi

DEST_PATH="${DEST_DIR}/${CLEAN_FILENAME}"

# Check if file already exists
if [[ -f "${DEST_PATH}" ]]; then
  echo "🟡 File already exists: ${DEST_PATH}"
  read -rp "Overwrite? (y/N): " OVERWRITE
  if [[ ! "${OVERWRITE}" =~ ^[Yy]$ ]]; then
    echo "❌ Download cancelled."
    exit 0
  fi
  echo "📝 Backing up existing file..."
  mv "${DEST_PATH}" "${DEST_PATH}.bak.$(date +%Y%m%d%H%M%S)"
fi

# Download the model
echo ""
echo "⬇️  Downloading ${MODEL_TYPE} to ${DEST_PATH}..."

CURL_ARGS=(-L --fail --progress-bar)
if (( ${#AUTH_HEADERS[@]} > 0 )); then
  CURL_ARGS+=("${AUTH_HEADERS[@]}")
fi
CURL_ARGS+=(-o "${DEST_PATH}" "${MODEL_URL}")

# Execute download
if curl "${CURL_ARGS[@]}"; then
  echo ""
  echo "✅ Successfully downloaded ${MODEL_TYPE}!"
  echo "📁 Saved to: ${DEST_PATH}"
  echo ""
  echo "You can now use this ${MODEL_TYPE} in ComfyUI."
else
  echo "❌ Download failed."
  echo ""
  case "${ACCESS_PROVIDER}" in
    Civitai)
      echo "💡 Possible solutions:"
      echo "   • The model may require a Civitai account and API token"
      echo "   • Get your API token from: https://civitai.com/user/account"
      echo "   • Some models are restricted and require special permissions"
      echo "   • Try downloading manually from the web interface first"
      ;;
    "Hugging Face")
      echo "💡 Possible solutions:"
      echo "   • Ensure your Hugging Face token has the correct repository access"
      echo "   • Hugging Face private repos require the read scope token"
      echo "   • Confirm the URL points to the raw file (e.g., /resolve/main/...)"
      echo "   • Try downloading with huggingface-cli if the issue persists"
      ;;
    *)
      ;;
  esac
  exit 2
fi
