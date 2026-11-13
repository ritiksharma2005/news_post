#!/bin/bash
# Trigger NEWS NIT IIT video generation pipeline
# Usage:
#   sh scripts/run_pipeline.sh <INSTAGRAM_URL_OR_ID>

set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$PROJECT_ROOT"

if [ -z "$1" ]; then
  echo "Usage: sh scripts/run_pipeline.sh <INSTAGRAM_URL>"
  echo "Example: sh scripts/run_pipeline.sh https://www.instagram.com/p/DB_xyz123/"
  exit 1
fi

echo "🎬 Starting NEWS NIT IIT Video Generation Pipeline..."
python3 -m news_anchor_ai.main --source instagram --url "$1"
