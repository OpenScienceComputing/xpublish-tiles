#!/usr/bin/env bash
set -euo pipefail

# Guard against sourcing this script (which would affect the current shell)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    : # Running as a script, which is correct
else
    echo "ERROR: Do not source this script. Run it directly: ./deploy/deploy.sh"
    return 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables
source "$SCRIPT_DIR/env.sh"

# Validate AWS credentials
if ! aws sts get-caller-identity --profile "${AWS_PROFILE:-default}" &>/dev/null; then
    echo "ERROR: AWS credentials not found for profile '${AWS_PROFILE:-default}'."
    echo "Run: aws configure --profile ${AWS_PROFILE:-default}"
    exit 1
fi
echo "AWS credentials OK."

# Validate Cloudflare token
if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
    echo "ERROR: CLOUDFLARE_API_TOKEN is not set in env.sh"
    exit 1
fi
echo "Cloudflare token OK."

# Set up conda
CONDA_BASE="$(conda info --base 2>/dev/null)" || { echo "ERROR: conda not found"; exit 1; }
source "$CONDA_BASE/etc/profile.d/conda.sh"

# Create conda environment if it doesn't exist
if ! conda env list | grep -q "^xpublish-tiles-deploy "; then
    echo "Creating conda environment..."
    conda env create -f "$SCRIPT_DIR/environment.yml"
fi
conda activate xpublish-tiles-deploy

# Ensure latest CDK CLI is installed
npm install -g aws-cdk@latest

# Run deploy
cd "$SCRIPT_DIR"
python deploy.py
