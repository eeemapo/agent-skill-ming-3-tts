#!/usr/bin/env python3
"""agent-skill-ming-3-tts: speak text through a `ming-tts` (Ming-3.0-tts-0.5B) endpoint.

The endpoint and key are supplied by the environment (or flags), so nothing
deployment-specific lives in this file:

    export MING_TTS_BASE_URL="https://llama-swap.example.com/v1"
    export MING_TTS_API_KEY="<your key>"   # inject from a secrets manager instead
                                           # of exporting it in a shell

Usage:
    python3 ming_tts.py --input "TEXT" [--output out.wav] [--language en]
                        [--options '{"template_name":"emotion","emotion":"高兴"}']
                        [--voice my-voice | --voice-ref /path/to/reference.wav]
                        [--reference-text "..."] [--seed 7] [--max-tokens 1000]

Outputs `audio/wav` (16-bit PCM, 44100 Hz mono) by default. `--output` writes
a file; omit it for raw bytes on stdout. Diagnostics always go to stderr.

Every model control belongs in the request's `options` map (or use the
convenience flags, which merge into it). `--options` wins over the flags.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL_ENV = "MING_TTS_BASE_URL"
API_KEY_ENV = "MING_TTS_API_KEY"

# Convenience flag -> options-map key. Values are merged into `options`.
OPTION_FLAGS = {
    "language": "language",
    "template_name": "template_name",
    "instruct": "instruct",
    "emotion": "emotion",
    "dialect": "dialect",
    "voice_id": "voice_id",
    "speed": "speed",
    "pitch": "pitch",
    "volume": "volume",
    "seed": "seed",
    "max_tokens": "max_tokens",
    "guidance_scale": "guidance_scale",
    "sigma": "sigma",
    "temperature": "temperature",
    "text_chunk_size": "text_chunk_size",
    "instruction_schema": "instruction_schema",
}


def die(message: str, code: int = 2) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Speak text with a ming-tts endpoint.")
    parser.add_argument("--input", help="text to speak (or use --input-file)")
    parser.add_argument("--input-file", help="read the text from a file ('-' = stdin)")
    parser.add_argument("--output", help="output file; omit for raw bytes on stdout")
    parser.add_argument("--model", default="ming-tts",
                        help="model id on the endpoint (default ming-tts)")
    parser.add_argument("--base-url", default=None,
                        help=f"endpoint base URL (default: ${BASE_URL_ENV}), "
                             "e.g. https://llama-swap.example.com/v1")
    parser.add_argument("--options",
                        help="model options as a JSON object (e.g. '{\"language\":\"en\"}')")
    parser.add_argument("--options-file", help="read the options JSON from a file")
    parser.add_argument("--voice", help="server-side voice name (library entry or preset)")
    parser.add_argument("--voice-ref",
                        help="reference WAV: a server-side library path (passes "
                             "through) or a local file (sent inline as base64)")
    parser.add_argument("--reference-text",
                        help="transcript of the reference WAV (enables the acoustic prefix)")
    parser.add_argument("--response-format", default=None,
                        help="wav (default), mp3, or json")
    parser.add_argument("--raw-text", action="store_true",
                        help="send text as one fragment (no chunking)")
    parser.add_argument("--zero-speaker-embedding", action="store_true",
                        help="use a zero speaker row (reference-free generation)")
    parser.add_argument("--timeout", type=float, default=240.0,
                        help="request timeout in seconds (default 240)")
    typed = {
        "seed": int, "max-tokens": int, "text-chunk-size": int,
        "guidance-scale": float, "sigma": float, "temperature": float,
    }
    for flag in ("language", "template-name", "instruct", "emotion", "dialect",
                 "voice-id", "speed", "pitch", "volume", "seed", "max-tokens",
                 "guidance-scale", "sigma", "temperature", "text-chunk-size",
                 "instruction-schema"):
        parser.add_argument(f"--{flag}", dest=flag.replace("-", "_"),
                            default=None, type=typed.get(flag))
    return parser.parse_args()


def load_text(args: argparse.Namespace) -> str:
    if args.input is not None and args.input_file is not None:
        die("use either --input or --input-file, not both")
    if args.input is not None:
        return args.input
    if args.input_file is None:
        die("--input \"TEXT\" or --input-file is required")
    if args.input_file == "-":
        return sys.stdin.read()
    with open(args.input_file, "r", encoding="utf-8") as handle:
        return handle.read()


def build_options(args: argparse.Namespace) -> dict:
    options: dict = {}
    if args.options_file:
        with open(args.options_file, "r", encoding="utf-8") as handle:
            options.update(json.load(handle))
    if args.options:
        try:
            parsed = json.loads(args.options)
        except json.JSONDecodeError as error:
            die(f"--options is not valid JSON: {error}")
        if not isinstance(parsed, dict):
            die("--options must be a JSON object")
        options.update(parsed)

    for flag, key in OPTION_FLAGS.items():
        value = getattr(args, flag, None)
        if value is not None:
            options.setdefault(key, value)
    if args.raw_text:
        options.setdefault("raw_text", True)
    if args.zero_speaker_embedding:
        options.setdefault("zero_speaker_embedding", True)
    return options


def voice_ref_value(raw: str) -> object:
    """Server-side library paths pass through; local files are sent inline."""
    if raw.startswith("/voices/"):
        return raw  # shared server-side reference library, when the endpoint has one
    if not os.path.exists(raw):
        # Not a local file: let the server resolve it (preset or server path).
        return raw
    with open(raw, "rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("ascii")
    return {"type": "base64", "data": encoded}


def main() -> int:
    args = parse_args()
    base_url = args.base_url or os.environ.get(BASE_URL_ENV)
    if not base_url:
        die(f"no endpoint configured. Pass --base-url or set ${BASE_URL_ENV} "
            "(e.g. https://llama-swap.example.com/v1).")
    key = os.environ.get(API_KEY_ENV)
    if not key:
        die(f"${API_KEY_ENV} is not set. Inject it from your secrets manager "
            "(or export it) before running.")

    body: dict = {"model": args.model, "input": load_text(args)}
    options = build_options(args)
    if options:
        body["options"] = options
    if args.voice:
        body["voice"] = args.voice
    if args.voice_ref:
        body["voice_ref"] = voice_ref_value(args.voice_ref)
    if args.reference_text:
        body["reference_text"] = args.reference_text
    if args.response_format:
        body["response_format"] = args.response_format

    url = base_url.rstrip("/") + "/audio/speech"
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        method="POST",
    )

    print(f"POST {url}  model={args.model}  "
          f"options={json.dumps(options, ensure_ascii=False)}", file=sys.stderr)
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            payload = response.read()
            status = response.status
            content_type = response.headers.get("content-type", "")
            duration = response.headers.get("x-audiocpp-audio-duration-ms")
            rtf = response.headers.get("x-audiocpp-rtf")
            wall = response.headers.get("x-audiocpp-wall-ms")
    except urllib.error.HTTPError as error:
        print(f"HTTP {error.code}: {error.read().decode('utf-8', 'replace')}",
              file=sys.stderr)
        return 1
    except urllib.error.URLError as error:
        die(f"request failed: {error.reason}", 1)

    audio = payload
    if "application/json" in content_type:
        parsed = json.loads(payload)
        encoded = parsed.get("audio")
        if encoded:
            audio = base64.b64decode(encoded)
        timing = parsed.get("timing") or {}
        duration = duration or timing.get("audio_duration_ms")
        rtf = rtf or timing.get("rtf")
        wall = wall or timing.get("wall_ms")
    print(f"http={status} content-type={content_type} bytes={len(audio)} "
          f"duration_ms={duration} rtf={rtf} wall_ms={wall}", file=sys.stderr)

    if args.output:
        with open(args.output, "wb") as handle:
            handle.write(audio)
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.buffer.write(audio)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
