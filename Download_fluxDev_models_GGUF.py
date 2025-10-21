# --- START OF Download_fluxDev_models(GGUF).py ---

import os
import sys
import zipfile
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import (
    RepositoryNotFoundError,
    EntryNotFoundError,
    HfHubHTTPError,
    LocalEntryNotFoundError
)

# --- Configuration ---
BASE_DOWNLOAD_DIR = "ComfyUI/models"
USE_SYMLINKS = False  # Copy files for compatibility

# VRAM-based GGUF model options for unet (flux1-dev and flux1-fill-dev)
VRAM_OPTIONS = {
    "8gb": [
        {"filename": "flux1-krea-dev-Q2_K.gguf", "fill_filename": "", "quant": "Q2_K", "krea": True},
        {"filename": "flux1-dev-Q3_K_S.gguf", "fill_filename": "flux1-fill-dev-Q3_K_S.gguf", "quant": "Q3_K_S"},
        {"filename": "flux1-krea-dev-Q3_K_S.gguf", "fill_filename": "", "quant": "Q3_K_S", "krea": True},
        {"filename": "flux1-krea-dev-Q3_K_M.gguf", "fill_filename": "", "quant": "Q3_K_M", "krea": True}
    ],
    "12gb": [
        {"filename": "flux1-dev-Q4_0.gguf", "fill_filename": "flux1-fill-dev-Q4_0.gguf", "quant": "Q4_0"},
        {"filename": "flux1-dev-Q4_1.gguf", "fill_filename": "flux1-fill-dev-Q4_1.gguf", "quant": "Q4_1"},
        {"filename": "flux1-dev-Q4_K_S.gguf", "fill_filename": "flux1-fill-dev-Q4_K_S.gguf", "quant": "Q4_K_S"},
        {"filename": "flux1-dev-Q5_0.gguf", "fill_filename": "flux1-fill-dev-Q5_0.gguf", "quant": "Q5_0"},
        {"filename": "flux1-dev-Q5_1.gguf", "fill_filename": "flux1-fill-dev-Q5_1.gguf", "quant": "Q5_1"},
        {"filename": "flux1-dev-Q5_K_S.gguf", "fill_filename": "flux1-fill-dev-Q5_K_S.gguf", "quant": "Q5_K_S"},
        {"filename": "flux1-krea-dev-Q4_0.gguf", "fill_filename": "", "quant": "Q4_0", "krea": True},
        {"filename": "flux1-krea-dev-Q4_1.gguf", "fill_filename": "", "quant": "Q4_1", "krea": True},
        {"filename": "flux1-krea-dev-Q4_K_M.gguf", "fill_filename": "", "quant": "Q4_K_M", "krea": True},
        {"filename": "flux1-krea-dev-Q4_K_S.gguf", "fill_filename": "", "quant": "Q4_K_S", "krea": True},
        {"filename": "flux1-krea-dev-Q5_0.gguf", "fill_filename": "", "quant": "Q5_0", "krea": True},
        {"filename": "flux1-krea-dev-Q5_1.gguf", "fill_filename": "", "quant": "Q5_1", "krea": True},
        {"filename": "flux1-krea-dev-Q5_K_M.gguf", "fill_filename": "", "quant": "Q5_K_M", "krea": True},
        {"filename": "flux1-krea-dev-Q5_K_S.gguf", "fill_filename": "", "quant": "Q5_K_S", "krea": True}
    ],
    "16gb": [
        {"filename": "flux1-krea-dev-Q5_K_M.gguf", "fill_filename": "", "quant": "Q5_K_M", "krea": True},
        {"filename": "flux1-krea-dev-Q5_K_S.gguf", "fill_filename": "", "quant": "Q5_K_S", "krea": True},
        {"filename": "flux1-dev-Q6_K.gguf", "fill_filename": "flux1-fill-dev-Q6_K.gguf", "quant": "Q6_K"},
        {"filename": "flux1-krea-dev-Q6_K.gguf", "fill_filename": "", "quant": "Q6_K", "krea": True}
    ],
    "24gb": [
        {"filename": "flux1-krea-dev-Q6_K.gguf", "fill_filename": "", "quant": "Q6_K", "krea": True},
        {"filename": "flux1-dev-Q8_0.gguf", "fill_filename": "flux1-fill-dev-Q8_0.gguf", "quant": "Q8_0"},
        {"filename": "flux1-krea-dev-Q8_0.gguf", "fill_filename": "", "quant": "Q8_0", "krea": True}
    ]
}

# T5 encoder GGUF models for clip, mapped by quantization
T5_ENCODER_MODELS = {
    "Q2_K": "t5-v1_1-xxl-encoder-Q3_K_S.gguf",  # Closest match for Q2_K
    "Q3_K_S": "t5-v1_1-xxl-encoder-Q3_K_S.gguf",
    "Q3_K_M": "t5-v1_1-xxl-encoder-Q4_K_M.gguf",  # Closest match for Q3_K_M
    "Q4_0": "t5-v1_1-xxl-encoder-Q4_K_M.gguf",  # Closest match for Q4_0
    "Q4_1": "t5-v1_1-xxl-encoder-Q4_K_M.gguf",
    "Q4_K_S": "t5-v1_1-xxl-encoder-Q4_K_M.gguf",
    "Q4_K_M": "t5-v1_1-xxl-encoder-Q4_K_M.gguf",
    "Q5_0": "t5-v1_1-xxl-encoder-Q5_K_S.gguf",
    "Q5_1": "t5-v1_1-xxl-encoder-Q5_K_S.gguf",
    "Q5_K_S": "t5-v1_1-xxl-encoder-Q5_K_S.gguf",
    "Q5_K_M": "t5-v1_1-xxl-encoder-Q5_K_S.gguf",  # Closest match for Q5_K_M
    "Q6_K": "t5-v1_1-xxl-encoder-Q6_K.gguf",
    "Q8_0": "t5-v1_1-xxl-encoder-Q8_0.gguf"
}

# Base download tasks (excluding unet and t5 encoder, which are handled separately)
DOWNLOAD_TASKS = [
    # --- controlnet ---
    {
        "repo_id": "simwalo/FluxDevFP8",
        "repo_type": "dataset",
        "filename": "Flux-Union-Pro2.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "controlnet")
    },
    {
        "repo_id": "simwalo/FluxDevFP8",
        "repo_type": "dataset",
        "filename": "Flux1-controlnet-upscaler-Jasperai-fp8.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "controlnet")
    },
    {
        "repo_id": "Nap/Qwen2VL-Flux-ControlNet",
        "repo_type": "model",
        "filename": "qwen2vl_flux_controlnet_bf16.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "controlnet")
    },
    # --- clip (non-quantized models) ---
    {
        "repo_id": "simwalo/FluxDevFP8",
        "repo_type": "dataset",
        "filename": "clip_l.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "clip")
    },
    {
        "repo_id": "simwalo/FluxDevFP8",
        "repo_type": "dataset",
        "filename": "ViT-L-14-TEXT-detail-improved-hiT-GmP-TE-only-HF.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "clip")
    },
    # --- vae ---
    {
        "repo_id": "simwalo/FluxDevFP8",
        "repo_type": "dataset",
        "filename": "ae.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "vae")
    },
    # --- loras ---
    {
        "repo_id": "simwalo/FluxDevFP8",
        "repo_type": "dataset",
        "filename": "comfyui_portrait_lora64.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "loras")
    },
    {
        "repo_id": "simwalo/FluxDevFP8",
        "repo_type": "dataset",
        "filename": "Maya_Lora_v1_000002500.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "loras")
    },
    {
        "repo_id": "simwalo/FluxDevFP8",
        "repo_type": "dataset",
        "filename": "more_details.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "loras")
    },
            {
        "repo_id": "simwalo/FluxDevFP8",
        "repo_type": "dataset",
        "filename": "FameGrid_Bold_SDXL_V1.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "loras")
    },
    {
        "repo_id": "simwalo/FluxDevFP8",
        "repo_type": "dataset",
        "filename": "fluxgram_lora_v1.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "loras")
    },
    # --- checkpoints ---
    {
        "repo_id": "simwalo/FluxDevFP8",
        "repo_type": "dataset",
        "filename": "epicrealism_naturalSinRC1VAE.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "checkpoints")
    },
    {
        "repo_id": "simwalo/FluxDevFP8",
        "repo_type": "dataset",
        "filename": "epicrealism_pureEvolutionV3.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "checkpoints")
    },
        {
        "repo_id": "simwalo/FluxDevFP8",
        "repo_type": "dataset",
        "filename": "epicrealismXL_vxviLastfameRealism.safetensors",
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "checkpoints")
    },
    # --- ZIP files (extract and delete) ---
    {
        "repo_id": "simwalo/custom_nodes",
        "repo_type": "dataset",
        "filename": "PersonMaskUltraV2.zip",
        "local_dir": BASE_DOWNLOAD_DIR,
        "extract_and_delete": True
    },
    {
        "repo_id": "simwalo/custom_nodes",
        "repo_type": "dataset",
        "filename": "insightface.zip",
        "local_dir": BASE_DOWNLOAD_DIR,
        "extract_and_delete": True
    },
    {
        "repo_id": "simwalo/custom_nodes",
        "repo_type": "dataset",
        "filename": "liveportrait.zip",
        "local_dir": BASE_DOWNLOAD_DIR,
        "extract_and_delete": True
    },
    {
        "repo_id": "simwalo/custom_nodes",
        "repo_type": "dataset",
        "filename": "rembg.zip",
        "local_dir": BASE_DOWNLOAD_DIR,
        "extract_and_delete": True
    },   {
        "repo_id": "simwalo/custom_nodes",
        "repo_type": "dataset",
        "filename": "LLM.zip",
        "local_dir": BASE_DOWNLOAD_DIR,
        "extract_and_delete": True
    },
    {
    "repo_id": "simwalo/custom_nodes",
    "repo_type": "dataset",
    "filename": "sams.zip",
    "local_dir": BASE_DOWNLOAD_DIR,
    "extract_and_delete": True
    },
    
   # --- New task for ComfyUI-LatentSyncWrapper.zip ---
    {
        "repo_id": "simwalo/custom_nodes",
        "repo_type": "dataset",
        "filename": "ComfyUI-LatentSyncWrapper.zip",
        "local_dir": "ComfyUI/custom_nodes",
        "extract_and_delete": True
    },
            {
        "repo_id": "simwalo/custom_nodes",
        "repo_type": "dataset",
        "filename": "comfyui-reactor.zip",
        "local_dir": "ComfyUI/custom_nodes",
        "extract_and_delete": True
    },
        {
        "repo_id": "simwalo/custom_nodes",
        "repo_type": "dataset",
        "filename": "Joy_caption_two.zip",
        "local_dir": "ComfyUI/models",
        "extract_and_delete": True
    },
    {
        "repo_id": "simwalo/SDXL",
        "repo_type": "model",
        "filename": "Text_Processor_By_Aiconomist.zip",
        "local_dir": "ComfyUI/custom_nodes",
        "extract_and_delete": True
    },
        {
        "repo_id": "simwalo/custom_nodes",
        "repo_type": "dataset",
        "filename": "sd-perturbed-attention-master.zip",
        "local_dir": "ComfyUI/custom_nodes",
        "extract_and_delete": True
    },
        {
        "repo_id": "simwalo/custom_nodes",
        "repo_type": "dataset",
        "filename": "siglip-so400m-patch14-384.zip",
        "local_dir": "ComfyUI/clip_vision",
        "extract_and_delete": True
    }
]
]

def get_user_vram_choice():
    """Prompts user to select VRAM and GGUF model, returns selected models and quantization."""
    print("\nSelect your NVIDIA GPU VRAM:")
    print("1. 8GB")
    print("2. 12GB")
    print("3. 16GB")
    print("4. 24GB+")
    while True:
        choice = input("Enter choice (1-4): ").strip()
        if choice == "1":
            vram = "8gb"
            break
        elif choice == "2":
            vram = "12gb"
            break
        elif choice == "3":
            vram = "16gb"
            break
        elif choice == "4":
            vram = "24gb"
            break
        print("Invalid choice. Please enter 1, 2, 3, or 4.")

    print(f"\nAvailable GGUF models for {vram.upper()} VRAM:")
    for i, model in enumerate(VRAM_OPTIONS[vram], 1):
        model_type = " (Krea)" if model.get("krea", False) else ""
        print(f"{i}. {model['filename']} (Quant: {model['quant']}){model_type}")
    
    while True:
        model_choice = input(f"Enter model number (1-{len(VRAM_OPTIONS[vram])}): ").strip()
        try:
            model_idx = int(model_choice) - 1
            if 0 <= model_idx < len(VRAM_OPTIONS[vram]):
                selected_model = VRAM_OPTIONS[vram][model_idx]
                is_krea = selected_model.get("krea", False)
                return selected_model["filename"], selected_model["fill_filename"], selected_model["quant"], is_krea
            print(f"Invalid choice. Please enter a number between 1 and {len(VRAM_OPTIONS[vram])}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def download_and_process_item(repo_id, local_dir, filename, use_symlinks=False, extract_and_delete=False, repo_type=None):
    """
    Downloads a file from a Hugging Face repository and optionally extracts and deletes ZIP files.

    Args:
        repo_id (str): Hugging Face repository ID.
        local_dir (str): Target directory for the file.
        filename (str): Specific file to download.
        use_symlinks (bool): Controls symlink behavior.
        extract_and_delete (bool): If True, extract ZIP file and delete it.
        repo_type (str): Type of repository ('dataset', 'model', etc.).

    Returns:
        bool: True if successful, False otherwise.
    """
    print("-" * 20)
    os.makedirs(local_dir, exist_ok=True)

    try:
        print(f"Downloading file:\n  Repo: {repo_id}\n  File: {filename}\n  To:   {local_dir}\n  Symlinks: {use_symlinks}\n  Repo Type: {repo_type or 'default'}")
        file_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=local_dir,
            local_dir_use_symlinks=use_symlinks,
            resume_download=True,
            repo_type=repo_type
            # token="your_hf_token_here"  # Uncomment and add token if repository is private/gated
        )
        print(f"Successfully downloaded: {file_path}")

        if extract_and_delete and filename.lower().endswith('.zip'):
            print(f"Extracting ZIP file: {file_path}")
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(local_dir)
            print(f"Extracted contents to: {local_dir}")
            print(f"Deleting ZIP file: {file_path}")
            os.remove(file_path)
            print(f"Deleted ZIP file: {file_path}")

        print("-" * 20)
        return True

    except RepositoryNotFoundError as e:
        print(f"\nError: Repository not found for '{repo_id}'. Details: {e}", file=sys.stderr)
    except EntryNotFoundError:
        print(f"\nError: File '{filename}' not found in repo '{repo_id}'.", file=sys.stderr)
    except LocalEntryNotFoundError as e:
        print(f"\nError: Local file system issue for '{repo_id}' in '{local_dir}'. Details: {e}", file=sys.stderr)
    except HfHubHTTPError as e:
        print(f"\nError: HTTP error for repo '{repo_id}'. Status: {e.response.status_code}. Details: {e}", file=sys.stderr)
    except zipfile.BadZipFile:
        print(f"\nError: File '{filename}' is not a valid ZIP file.", file=sys.stderr)
    except Exception as e:
        print(f"\nError: Unexpected error downloading '{filename}' from '{repo_id}': {type(e).__name__} - {e}", file=sys.stderr)

    print("-" * 20)
    return False

def main():
    """Downloads FluxDev GGUF models based on user VRAM selection and other specified files."""
    print("Starting FluxDev GGUF model and custom node downloads...")
    print(f"Base download directory: {os.path.abspath(BASE_DOWNLOAD_DIR)}")
    print(f"Symlinks: {'Enabled' if USE_SYMLINKS else 'Disabled (copying files)'}")

    # Get user's VRAM and model choice
    unet_filename, fill_filename, quant_level, is_krea = get_user_vram_choice()
    t5_filename = T5_ENCODER_MODELS.get(quant_level, "t5-v1_1-xxl-encoder-Q4_K_M.gguf")  # Fallback if quant not found

    # Add unet and t5 encoder tasks
    tasks = []
    
    # Add main unet model based on whether it's Krea or regular
    if is_krea:
        tasks.append({
            "repo_id": "QuantStack/FLUX.1-Krea-dev-GGUF",
            "repo_type": "model",
            "filename": unet_filename,
            "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "unet")
        })
    else:
        tasks.extend([
            {
                "repo_id": "city96/FLUX.1-dev-gguf",
                "repo_type": "model",
                "filename": unet_filename,
                "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "unet")
            },
            {
                "repo_id": "YarvixPA/FLUX.1-Fill-dev-gguf",
                "repo_type": "model",
                "filename": fill_filename,
                "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "unet")
            }
        ])
    
    # Add T5 encoder (common for both)
    tasks.append({
        "repo_id": "city96/t5-v1_1-xxl-encoder-gguf",
        "repo_type": "model",
        "filename": t5_filename,
        "local_dir": os.path.join(BASE_DOWNLOAD_DIR, "clip")
    })
    
    tasks = tasks + DOWNLOAD_TASKS  # Combine with base tasks

    successful_downloads = 0
    failed_downloads = 0

    for i, task in enumerate(tasks, 1):
        print(f"\n--- Task {i}/{len(tasks)} ---")
        repo_id = task.get("repo_id")
        local_dir = task.get("local_dir")
        filename = task.get("filename")
        repo_type = task.get("repo_type")

        if not all([repo_id, local_dir, filename]):
            print(f"Error: Task {i} is missing required fields. Skipping.", file=sys.stderr)
            failed_downloads += 1
            continue

        success = download_and_process_item(
            repo_id=repo_id,
            local_dir=local_dir,
            filename=filename,
            use_symlinks=USE_SYMLINKS,
            extract_and_delete=task.get("extract_and_delete", False),
            repo_type=repo_type
        )
        if success:
            successful_downloads += 1
        else:
            failed_downloads += 1
            print(f"Continuing with next task despite error...")

    print("\n" + "=" * 30)
    print("--- Download Summary ---")
    if is_krea:
        print(f"Selected flux1-krea-dev model: {unet_filename} (Quant: {quant_level})")
    else:
        print(f"Selected flux1-dev model: {unet_filename} (Quant: {quant_level})")
        print(f"Selected flux1-fill-dev model: {fill_filename} (Quant: {quant_level})")
    print(f"Selected t5 encoder model: {t5_filename}")
    print(f"Successful tasks: {successful_downloads}")
    print(f"Failed tasks: {failed_downloads}")
    print("=" * 30)

    if failed_downloads > 0:
        print("\nWarning: One or more tasks failed. Check error messages above.")
        sys.exit(1)
    else:
        print("\nAll tasks completed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()

# --- END OF Download_fluxDev_models(GGUF).py ---