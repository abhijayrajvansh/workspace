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

# Check if this is a Civitai URL and get API token if needed
CIVITAI_TOKEN=""
if [[ "${MODEL_URL}" == *"civitai.com"* ]]; then
  echo ""
  echo "🔑 This is a Civitai URL. Some models require authentication."
  read -rp "Enter your Civitai API token (optional, press Enter to skip): " CIVITAI_TOKEN
  echo "💡 Tip: Get your API token from https://civitai.com/user/account"
fi

# Get model type
echo ""
echo "Select model type:"
echo "1) Checkpoint"
echo "2) LoRA"
echo ""
read -rp "Enter choice (1 or 2): " MODEL_TYPE_CHOICE
if [[ -z "${MODEL_TYPE_CHOICE}" ]]; then
  echo "❌ Model type choice is required."
  exit 1
fi

case "${MODEL_TYPE_CHOICE}" in
  1)
    MODEL_TYPE="checkpoint"
    DEST_DIR="./ComfyUI/models/checkpoints"
    ;;
  2)
    MODEL_TYPE="lora"
    DEST_DIR="./ComfyUI/models/loras"
    ;;
  *)
    echo "❌ Invalid choice. Please select 1 or 2."
    exit 1
    ;;
esac

# Create destination directory
mkdir -p "${DEST_DIR}"

# Get output filename from user
echo ""
read -rp "Enter output filename (without extension): " USER_FILENAME
if [[ -z "${USER_FILENAME}" ]]; then
  echo "❌ Filename is required."
  exit 1
fi

# Validate filename (remove invalid characters and ensure it's safe)
validate_filename() {
  local filename="$1"
  
  # Remove invalid characters for filesystem
  filename=$(echo "${filename}" | sed 's/[<>:"/\\|?*]//g')
  
  # Remove leading/trailing spaces and dots
  filename=$(echo "${filename}" | sed 's/^[[:space:].]*//' | sed 's/[[:space:]]*$//')
  
  # Ensure filename is not empty after cleaning
  if [[ -z "${filename}" ]]; then
    echo "❌ Invalid filename. Please use only valid characters."
    exit 1
  fi
  
  echo "${filename}"
}

CLEAN_FILENAME=$(validate_filename "${USER_FILENAME}")
FILENAME="${CLEAN_FILENAME}.safetensors"

DEST_PATH="${DEST_DIR}/${FILENAME}"

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

# Prepare curl command with optional authorization
CURL_CMD="curl -L --fail -o \"${DEST_PATH}\""
if [[ -n "${CIVITAI_TOKEN}" ]]; then
  CURL_CMD="curl -L --fail -H \"Authorization: Bearer ${CIVITAI_TOKEN}\" -o \"${DEST_PATH}\""
fi

# Execute download
if eval "${CURL_CMD} \"${MODEL_URL}\""; then
  echo ""
  echo "✅ Successfully downloaded ${MODEL_TYPE}!"
  echo "📁 Saved to: ${DEST_PATH}"
  echo ""
  echo "You can now use this ${MODEL_TYPE} in ComfyUI."
else
  echo "❌ Download failed."
  echo ""
  if [[ "${MODEL_URL}" == *"civitai.com"* ]]; then
    echo "💡 Possible solutions:"
    echo "   • The model may require a Civitai account and API token"
    echo "   • Get your API token from: https://civitai.com/user/account"
    echo "   • Some models are restricted and require special permissions"
    echo "   • Try downloading manually from the web interface first"
  fi
  exit 2
fi
