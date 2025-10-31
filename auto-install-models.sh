#!/usr/bin/env bash
set -euo pipefail

# auto-install-models.sh — Install ComfyUI models listed in a JSON config.
# Usage: ./auto-install-models.sh path/to/models-config.json [base-directory]
#
# Config format: a JSON array of objects with the following required keys:
#   url       – Direct download link.
#   filename  – Final filename for the downloaded model.
#   dest      – Destination directory (relative to base directory unless absolute).
# Optional key:
#   overwrite – true/false to force re-download when the file already exists (default false).
#
# Example:
# [
#   {
#     "url": "https://huggingface.co/owner/repo/resolve/main/model.safetensors",
#     "filename": "model.safetensors",
#     "dest": "ComfyUI/models/checkpoints"
#   }
# ]
#
# Authentication:
#   Export environment variables before running the script to authenticate automatically:
#     export HF_TOKEN=your_huggingface_token
#     export CIVITAI_TOKEN=your_civitai_token
#   (Aliases EXPORT_HF_TOKEN / EXPORT_CIVITAI_TOKEN are also honoured.)

usage() {
  cat <<'USAGE'
Usage: ./auto-install-models.sh <config.json> [base-directory]
  config.json     Path to a JSON array describing model downloads.
  base-directory  Optional root for relative destinations (defaults to script directory).
USAGE
}

if [[ $# -lt 1 ]]; then
  echo "❌ Missing config file path." >&2
  usage
  exit 1
fi

CONFIG_PATH=$1
BASE_DIR_INPUT=${2:-}

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "❌ Config file not found: $CONFIG_PATH" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "❌ jq is required but was not found in PATH." >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "❌ curl is required but was not found in PATH." >&2
  exit 1
fi

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if [[ -z "$BASE_DIR_INPUT" ]]; then
  BASE_DIR=$SCRIPT_DIR
else
  if [[ "$BASE_DIR_INPUT" = /* ]]; then
    BASE_DIR=$BASE_DIR_INPUT
  else
    BASE_DIR="$SCRIPT_DIR/$BASE_DIR_INPUT"
  fi
fi

BASE_DIR=${BASE_DIR%/}

if ! jq -e 'type == "array"' "$CONFIG_PATH" >/dev/null; then
  echo "❌ Config file must contain a JSON array." >&2
  exit 1
fi

TOTAL_COUNT=$(jq 'length' "$CONFIG_PATH")
if [[ $TOTAL_COUNT -eq 0 ]]; then
  echo "ℹ️  Config file is empty. Nothing to install."
  exit 0
fi

sanitize_filename() {
  local filename=$1
  filename=$(printf '%s' "$filename" | sed 's/[<>:"\\/|?*]//g')
  filename=$(printf '%s' "$filename" | sed 's/^[[:space:].]*//; s/[[:space:]]*$//')
  printf '%s' "$filename"
}

lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

extract_host() {
  local url=$1
  url=${url#*://}
  url=${url%%/*}
  printf '%s' "$url"
}

warn() {
  printf '⚠️  %s\n' "$1" >&2
}

error_exit() {
  printf '❌ %s\n' "$1" >&2
  exit 1
}

HF_TOKEN_VALUE=${HF_TOKEN:-${EXPORT_HF_TOKEN:-}}
CIVITAI_TOKEN_VALUE=${CIVITAI_TOKEN:-${EXPORT_CIVITAI_TOKEN:-}}

echo "🤖 ComfyUI Model Auto-Installer"
echo "=============================="
echo "📄 Config: $CONFIG_PATH"
echo "📁 Base directory: $BASE_DIR"
echo "🧾 Total entries: $TOTAL_COUNT"
echo ""

SUCCESS_COUNT=0
SKIPPED_COUNT=0
FAIL_COUNT=0

while IFS= read -r row || [[ -n "$row" ]]; do
  index=$(echo "$row" | jq -r '.key')
  entry=$(echo "$row" | jq -c '.value')
  entry_no=$((index + 1))

  url=$(echo "$entry" | jq -r '.url // empty')
  dest=$(echo "$entry" | jq -r '.dest // empty')
  raw_filename=$(echo "$entry" | jq -r '.filename // empty')
  overwrite_raw=$(echo "$entry" | jq -r '.overwrite // empty')

  [[ -z "$url" ]] && error_exit "Entry #$entry_no is missing the required 'url' field."
  [[ -z "$dest" ]] && error_exit "Entry #$entry_no is missing the required 'dest' field."
  [[ -z "$raw_filename" ]] && error_exit "Entry #$entry_no is missing the required 'filename' field."

  if [[ "$dest" = /* ]]; then
    dest_dir=$dest
  else
    dest_dir="$BASE_DIR/$dest"
  fi
  dest_dir=${dest_dir%/}

  filename=$(sanitize_filename "$raw_filename")
  [[ -z "$filename" ]] && error_exit "Entry #$entry_no: Invalid filename after sanitization."

  dest_path="$dest_dir/$filename"

  overwrite="false"
  if [[ -n "$overwrite_raw" ]]; then
    case $(lower "$overwrite_raw") in
      true|1|yes|y|on)
        overwrite="true";;
      false|0|no|n|off)
        overwrite="false";;
      *)
        error_exit "Entry #$entry_no: Invalid overwrite value '$overwrite_raw'.";;
    esac
  fi

  mkdir -p "$dest_dir"

  if [[ -f "$dest_path" && "$overwrite" != "true" ]]; then
    echo "[$entry_no/$TOTAL_COUNT] ⏭️  Skipping existing file: $dest_path"
    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
    echo ""
    continue
  fi

  if [[ -f "$dest_path" && "$overwrite" == "true" ]]; then
    echo "[$entry_no/$TOTAL_COUNT] 📝 Overwriting existing file: $dest_path"
  else
    echo "[$entry_no/$TOTAL_COUNT] ⬇️  Downloading -> $dest_path"
  fi

  host=$(extract_host "$url")
  host_lower=$(lower "$host")

  curl_cmd=(curl -L --fail --progress-bar)

  if [[ $host_lower == *"huggingface.co"* ]]; then
    if [[ -n "$HF_TOKEN_VALUE" ]]; then
      curl_cmd+=("-H" "Authorization: Bearer $HF_TOKEN_VALUE")
    fi
  elif [[ $host_lower == *"civitai.com"* ]]; then
    if [[ -n "$CIVITAI_TOKEN_VALUE" ]]; then
      curl_cmd+=("-H" "Authorization: Bearer $CIVITAI_TOKEN_VALUE")
    fi
  fi

  tmp_path="$dest_path.partial-$$"
  curl_cmd+=(-o "$tmp_path" "$url")

  if "${curl_cmd[@]}"; then
    mv "$tmp_path" "$dest_path"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    echo "[$entry_no/$TOTAL_COUNT] ✅ Stored at $dest_path"
  else
    rm -f "$tmp_path"
    echo "[$entry_no/$TOTAL_COUNT] ❌ Download failed for $url" >&2
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
  echo ""

done < <(jq -c 'to_entries[]' "$CONFIG_PATH")

if [[ $FAIL_COUNT -gt 0 ]]; then
  echo "⚠️  Completed with failures: $FAIL_COUNT entries failed, $SUCCESS_COUNT succeeded, $SKIPPED_COUNT skipped." >&2
  exit 1
fi

echo "🎉 All downloads complete. $SUCCESS_COUNT succeeded, $SKIPPED_COUNT skipped."
exit 0
