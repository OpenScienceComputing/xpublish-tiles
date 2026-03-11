#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables
source "$SCRIPT_DIR/env.sh"

# Create conda environment if it doesn't exist
eval "$(conda shell.bash hook)"
if ! conda env list | grep -q "^xpublish-tiles-deploy "; then
    conda env create -f "$SCRIPT_DIR/environment.yml"
fi
conda activate xpublish-tiles-deploy

# Ensure latest CDK CLI is installed
npm install -g aws-cdk@latest

# Run deploy
cd "$SCRIPT_DIR"
python deploy.py
