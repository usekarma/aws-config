#!/bin/bash
set -euo pipefail

# Usage: AWS_PROFILE=your-profile ./deploy.sh <component> <nickname>

if [[ $# -ne 2 ]]; then
  echo "Usage: AWS_PROFILE=your-profile ./deploy.sh <component> <nickname>"
  exit 1
fi

COMPONENT="$1"
NICKNAME="$2"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/deploy_config.py" --component "$COMPONENT" --nickname "$NICKNAME"
