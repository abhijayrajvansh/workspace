"""Downloader for Stable Diffusion 3.5 Base assets for ComfyUI."""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Iterable, Optional

from huggingface_hub import HfFolder, snapshot_download
from huggingface_hub.utils import HfHubHTTPError, LocalEntryNotFoundError, RepositoryNotFoundError

DEFAULT_REPO_ID = "stabilityai/stable-diffusion-3.5-base"

ALLOW_PATTERNS: tuple[str, ...] = (
    "*.safetensors",
    "*.json",
    "scheduler/*.json",
    "transformer/*",
    "vae/*",
    "text_encoder/*",
    "text_encoder_2/*",
    "text_encoder_3/*",
    "text_encoders/*",
    "tokenizer/*",
    "tokenizer_2/*",
    "tokenizer_3/*",
)

TARGET_LAYOUT = (
    ("transformer", Path("ComfyUI/models/unet/sd35-base")),
    ("vae", Path("ComfyUI/models/vae/sd35-base")),
    ("text_encoder", Path("ComfyUI/models/clip/sd35-base/text_encoder")),
    ("text_encoder_2", Path("ComfyUI/models/clip/sd35-base/text_encoder_2")),
    ("text_encoder_3", Path("ComfyUI/models/clip/sd35-base/text_encoder_3")),
    ("text_encoders", Path("ComfyUI/models/clip/sd35-base/text_encoders")),
    ("tokenizer", Path("ComfyUI/models/clip/sd35-base/tokenizer")),
    ("tokenizer_2", Path("ComfyUI/models/clip/sd35-base/tokenizer_2")),
    ("tokenizer_3", Path("ComfyUI/models/clip/sd35-base/tokenizer_3")),
)

CHECKPOINT_TARGET = Path("ComfyUI/models/checkpoints")
MODEL_CONFIG_TARGET = Path("ComfyUI/models/checkpoints/sd35-base")


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Stable Diffusion 3.5 Base for ComfyUI")
    parser.add_argument(
        "--repo-id",
        default=DEFAULT_REPO_ID,
        help="Hugging Face repository ID for SD3.5 Base",
    )
    parser.add_argument(
        "--revision",
        default="main",
        help="Repository revision/branch/tag (default: main)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("HF_TOKEN") or HfFolder.get_token(),
        help="Hugging Face access token (defaults to $HF_TOKEN or cached login)",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Optional custom cache directory for Hugging Face downloads",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip copying files that already exist at the destination",
    )
    return parser.parse_args(argv)


def copy_file(src: Path, dst: Path, skip_existing: bool = False) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if skip_existing and dst.exists():
        print(f"[skip] {dst} already exists")
        return
    shutil.copy2(src, dst)
    print(f"[copy] {src} -> {dst}")


def copy_tree(src: Path, dst: Path, skip_existing: bool = False) -> None:
    if not src.exists():
        return
    for item in src.rglob("*"):
        if item.is_dir():
            continue
        relative = item.relative_to(src)
        target_path = dst / relative
        copy_file(item, target_path, skip_existing=skip_existing)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)

    token_display = "<set>" if args.token else "<none>"
    print("=== Stable Diffusion 3.5 Base Downloader ===")
    print(f"Repo: {args.repo_id}")
    print(f"Revision: {args.revision}")
    print(f"HF_TOKEN: {token_display}")
    print()

    try:
        snapshot_path = Path(
            snapshot_download(
                repo_id=args.repo_id,
                repo_type="model",
                revision=args.revision,
                token=args.token,
                cache_dir=args.cache_dir,
                allow_patterns=ALLOW_PATTERNS,
                local_dir_use_symlinks=False,
            )
        )
    except RepositoryNotFoundError as exc:
        print(f"❌ Repository not found: {exc}", file=sys.stderr)
        return 1
    except HfHubHTTPError as exc:
        print(f"❌ HTTP error while downloading: {exc}", file=sys.stderr)
        if exc.response is not None and exc.response.status_code == 401:
            print("Hint: Accept the model license on Hugging Face and provide a valid HF token.", file=sys.stderr)
        return 1
    except LocalEntryNotFoundError as exc:
        print(f"❌ Local cache error: {exc}", file=sys.stderr)
        return 1

    print(f"Downloaded snapshot to {snapshot_path}")

    # Copy root-level safetensors/checkpoints
    root_ckpts = list(snapshot_path.glob("*.safetensors"))
    if not root_ckpts:
        print("⚠️ No root-level .safetensors files found; continuing with subdirectories.")
    for ckpt in root_ckpts:
        target = CHECKPOINT_TARGET / ckpt.name
        copy_file(ckpt, target, skip_existing=args.skip_existing)

    # Copy model index and scheduler config for reference
    for filename in ("model_index.json",):
        src = snapshot_path / filename
        if src.exists():
            copy_file(src, MODEL_CONFIG_TARGET / filename, skip_existing=args.skip_existing)

    scheduler_dir = snapshot_path / "scheduler"
    if scheduler_dir.exists():
        copy_tree(scheduler_dir, MODEL_CONFIG_TARGET / "scheduler", skip_existing=args.skip_existing)

    # Copy directory buckets (transformer, vae, encoders, tokenizers)
    for relative_dir, target_base in TARGET_LAYOUT:
        src_dir = snapshot_path / relative_dir
        if not src_dir.exists():
            print(f"[warn] {relative_dir} not present in snapshot; skipping")
            continue
        print(f"Copying {relative_dir} -> {target_base}")
        copy_tree(src_dir, target_base, skip_existing=args.skip_existing)

    print("\n✅ Stable Diffusion 3.5 Base assets copied into ComfyUI models directory.")
    print("Restart ComfyUI or refresh its model list to pick up the new files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
