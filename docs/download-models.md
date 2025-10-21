# `download-models.sh` Reference

## Purpose
- Provide an interactive launcher that downloads ComfyUI-compatible Flux, Wan, and Stable Diffusion 3.5 model bundles on Linux.
- Centralize execution of the individual Python downloaders (`Download_*.py`) that perform authenticated Hugging Face transfers.

## High-Level Flow
1. Change directory to the location of the script so relative Python invocations work regardless of where it is launched from.
2. Locate a Python interpreter (`python3` preferred, fallback to `python`).
3. Ensure `pip` is present (`python -m ensurepip --upgrade` if missing).
4. Install or upgrade the Hugging Face transfer dependencies: `hf_transfer`, `huggingface_hub[cli,tqdm]`, and `huggingface_hub[hf_xet]`.
5. Present an interactive menu that dispatches to a specific Python downloader script based on the user's selection.
6. Pause after each run so the user can read success or error output.

## Prerequisites
- Linux shell with Bash 4+ (script uses `bash`-specific syntax and `set -euo pipefail`).
- Internet access to reach Hugging Face model repositories.
- Python 3.8+ recommended for up-to-date `pip` and dependency wheels.
- Adequate free disk space for downloaded models (tens of GB per model set) and sufficient GPU VRAM per the menu guidance.

## Installed Python Packages
- `hf_transfer`: Accelerates large binary downloads from Hugging Face.
- `huggingface_hub[cli,tqdm]`: Supplies the CLI client and progress bars used by the Python downloader scripts.
- `huggingface_hub[hf_xet]`: Adds support for `hf://` URLs that rely on the Xet backend.

## Menu Options and Backing Scripts
| Option | Label                                | Python Script                        | Notes |
|--------|--------------------------------------|--------------------------------------|-------|
| 1      | Flux Dev FP8                         | `Download_fluxDev_models_FP8.py`     | Targets GPUs with ≥24 GB VRAM.
| 2      | Flux Dev GGUF                        | `Download_fluxDev_models_GGUF.py`    | Compressed GGUF variant for ≤24 GB VRAM.
| 3      | Flux Kontext GGUF                    | `Download_models_Flux_Kontext_GGUF.py` | Kontext add-on models.
| 4      | Wan 2.1 GGUF InfiniteTalk            | `Download_models_GGUF.py`            | Speech-focused InfiniteTalk pack.
| 5      | Wan 2.1 Vace GGUF                    | `Download_models_GGUF_VACE.py`       | VACE variant tuned for VFX.
| 6      | Wan 2.1 Phantom GGUF                 | `Download_models_GGUF_PHANTOM.py`    | Phantom stylized model set.
| 7      | NSFW Lessons Models                  | `Download_models_NSFW.py`            | Adult-content models (opt-in).
| 8      | Wan 2.2 Text-to-Video (T2V)          | `Download_wan2-2_T2V.py`             | Requires newer Wan pipelines.
| 9      | Wan 2.2 Image-to-Video (I2V)         | `Download_wan2-2_I2V.py`             | Converts stills into short clips.
| 10     | Stable Diffusion 3.5 Base (ComfyUI)  | `Download_stable_diffusion_3_5_base.py` | Requires Hugging Face access token for the gated SD3.5 Base repo.
| 11     | Exit                                 | (built-in)                           | Closes the launcher.

## Runtime Behaviour
- Each selection verifies the corresponding Python file exists alongside the shell script before invoking it. Missing files surface a clear error message instead of failing silently.
- Python scripts inherit the `PYTHON` interpreter discovered earlier, ensuring a consistent runtime environment.
- The menu redraws after each downloader completes, allowing multiple model sets to be installed sequentially.
- `Ctrl+C` exits immediately because of `set -e`; partial downloads are handled inside the Python scripts.

## Known Quirks & Tips
- Stable Diffusion 3.5 Base is a gated Stability AI release. Accept the license on Hugging Face and set `HF_TOKEN` (or run `huggingface-cli login`) before launching option 10.
- If `pip` upgrades packages system-wide, you may need `--user` installs or a virtual environment when running on managed Linux systems.
- The script assumes the Python downloaders manage authentication (HF tokens) and destination directories; configure those scripts before running this launcher.
- To add new model bundles, copy an existing case block, change the menu label and script name, and ensure the new Python downloader lives next to `download-models.sh`.

## Example Usage
```bash
chmod +x download-models.sh
./download-models.sh
# Choose option 10 to pull Stable Diffusion 3.5 Base (requires HF_TOKEN)
```

## Related Files
- `Download_fluxDev_models_FP8.py`
- `Download_fluxDev_models_GGUF.py`
- `Download_models_Flux_Kontext_GGUF.py`
- `Download_models_GGUF*.py` variants for Wan 2.1 model families
- `Download_models_NSFW.py`
- `Download_wan2-2_T2V.py`
- `Download_wan2-2_I2V.py`
- `Download_stable_diffusion_3_5_base.py`

Keep this document in sync with the Python scripts so the menu description mirrors the actual download targets and prerequisites.
