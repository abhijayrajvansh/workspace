# Repository Guidelines

## Project Structure & Module Organization
Each top-level folder contains a standalone workflow exported from ComfyUI (for example, `Flux Fill FLux Redux Swap Clothes/` or `hyperlora/`). Inside, you'll find one or more `.json` graphs that define the node layout. Keep auxiliary assets (reference images, notes) alongside the workflow in the same folder and name them descriptively. Before adding a new directory, check for existing workflows that can be updated instead of duplicated.

## Documentation & Catalog
Keep the root `README.md` in sync with the workflow library. Every new or updated graph needs a one-line summary, the generation category (text-to-video, image-to-video, image editing, etc.), listed model stacks, and an NSFW flag if applicable.

## Build, Test, and Development Commands
There is no compile step; workflows must simply be valid JSON. Run `python -m json.tool "path/to/workflow.json"` after edits to ensure syntax correctness, and use `jq` for formatting tweaks when necessary. While iterating, load the graph into ComfyUI locally and confirm that all checkpoints, LoRAs, and control assets resolve.

## Coding Style & Naming Conventions
Format JSON with two-space indentation and sorted keys where ComfyUI preserves them. Use descriptive file names that match the workflow focus (e.g., `wan2.1-fusionx-image-to-video.json`). Prefer lowercase with hyphens and avoid spaces when creating new files to ease scripting. Document any non-standard nodes or required models in a short README inside the workflow folder.

## Testing Guidelines
Before submitting, execute a dry run in ComfyUI with sample prompts to ensure the graph renders without missing inputs. Update node defaults so the preview image renders successfully on first load. If a workflow includes multiple branches, capture representative outputs and store lightweight thumbnails (<500 KB) for reviewers.

## Commit & Pull Request Guidelines
Follow the existing commit style of an imperative verb followed by a colon (e.g., `added: flux face swap workflow`). Group related JSON adjustments into a single commit. Pull requests should summarize the creative goal, list new or updated folders, link to any dependent assets, and attach screenshots or short GIFs of key outputs. Mention required model hashes so reviewers can reproduce the results.
