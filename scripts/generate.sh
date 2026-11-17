#!/usr/bin/env bash
# Agent-Skill-Ming-3.0-TTS: compatibility shim for the old flag set.
#
# The endpoint and key come from the environment (see ming_tts.py):
#   MING_TTS_BASE_URL   e.g. https://llama-swap.example.com/v1
#   MING_TTS_API_KEY    injected from a secrets manager; never commit it
#
# Usage: generate.sh --input "TEXT" [--output FILE] [--model NAME] [--base-url URL]
#        (all other flags are passed through to scripts/ming_tts.py)
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/ming_tts.py" "$@"
