#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Step 1: Download the installer script
echo "Downloading installer script..."
curl -L "https://raw.githubusercontent.com/abhijayrajvansh/workspace/refs/heads/main/auto-install-models.sh" -o install.sh

# Step 2: Make the script executable
echo "Making script executable..."
chmod +x install.sh

# Step 3: Change to the target directory
echo "Changing directory to /workspace/ComfyUI/user/default..."
cd /workspace/ComfyUI/user/default || { echo "Directory not found!"; exit 1; }

# Step 4: Clone the workflows repository
echo "Cloning workflows repository..."
git clone https://github.com/abhijayrajvansh/workflows

# Step 5: Move models-config folder to workspace directory
echo "Moving models-config folder to /workspace..."
mv /workspace/ComfyUI/user/default/workflows/models-config /workspace/ || { echo "models-config folder not found!"; exit 1; }

echo "✅ All steps executed successfully!"

