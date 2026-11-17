---
name: agent-skill-ming-3.0-tts
description: Generate, clone, design, and control speech with Ming-3.0-tts-0.5B — the `ming-tts` model served by an OpenAI-compatible llama-swap / audio.cpp endpoint (POST /v1/audio/speech). Use for any TTS request against such an endpoint: plain narration, voice cloning from a reference WAV, built-in voices, emotion / speed / pitch / volume / dialect / multilingual control, voice design and freeform delivery instructions, and inline paralinguistic tags. Endpoint and API key come from the environment (MING_TTS_BASE_URL, MING_TTS_API_KEY); model controls go in the request's `options` map.
license: MIT
---

# agent-skill-ming-3.0-tts

Speak text through **`ming-tts`** — Ming-3.0-tts-0.5B (dense, Qwen2-based) served
by an OpenAI-compatible **llama-swap / audio.cpp** endpoint. The wire surface is
OpenAI-shaped (`POST /v1/audio/speech`), but every Ming control travels in the
request's **`options`** map, which the server validates against the model's spec.

This skill is deployment-agnostic: point it at any endpoint that serves the
model, and inject the key from your own secrets source.

## How to use this skill

| Your task involves... | Read this file first |
| :--- | :--- |
| Plain TTS, narration, reading text aloud, formats, long text | `patterns/generate-speech.md` |
| Emotion, speed/pitch/volume, dialect, multilingual, built-in voices, tags | `patterns/control-speech.md` |
| Voice cloning, voice libraries, voice design, freeform delivery | `patterns/clone-and-design.md` |
| Exact wire fields, the full options table, error catalog | `references/wire-api.md` |
| Voice ids, tag list, language map | `references/voice-catalog.md` |
| Upstream Python contract, model internals | `references/upstream-contract.md` |

## Quick start

Configure the endpoint and key in the environment (in an agent harness, inject
the key from a secrets manager rather than exporting it in a shell):

```
export MING_TTS_BASE_URL="https://llama-swap.example.com/v1"
export MING_TTS_API_KEY="<your key>"

python3 scripts/ming_tts.py \
  --input 'Good evening. The harbor is quiet tonight.' \
  --language en --output /tmp/out.wav
```

`scripts/ming_tts.py` builds the JSON body, sends it, and writes the audio
(stdout when `--output` is omitted). `scripts/generate.sh` is a compatibility
shim. `--options '<json>'` passes any model control; convenience flags
(`--emotion`, `--voice-id`, `--seed`, `--voice`, `--voice-ref`, …) merge into the
same map. `--base-url` overrides `MING_TTS_BASE_URL` per call.

## Endpoint facts

| | |
| :--- | :--- |
| Model id | `ming-tts` (the gateway's umbrella id, e.g. `audio`, is usually **not** a valid request model) |
| Base URL | `https://llama-swap.example.com/v1` — your deployment's address (Tailnet, LAN, or public) |
| Route | `POST /v1/audio/speech`, JSON body, `Authorization: Bearer $MING_TTS_API_KEY` |
| Response | `audio/wav` — 16-bit PCM, 44100 Hz mono (may also offer `mp3` or JSON base64) |
| Timing headers | `x-audiocpp-audio-duration-ms`, `x-audiocpp-rtf`, `x-audiocpp-wall-ms` |
| Backend | audio.cpp `ming3_tts` family; `rtf` ≈ 0.28 on a modern GPU |

## Control templates

`options.template_name` selects the conditioning template (default `tts`).
A template accepts only its matching controls.

| `template_name` | Controls (exact keys) | Values |
| :--- | :--- | :--- |
| `tts` (default) | optional `instruct`; inline `[Tags]` | — |
| `multilingual` | `language` (required) | `ja` `ko` `de` `fr` `es` (zh/en optional) |
| `basic` | `speed`, `pitch`, `volume` (send all three) | 慢速/中速/快速 · 低/中/高 · 低/中/高 |
| `emotion` | `emotion` | 高兴/悲伤/愤怒/恐惧/厌恶/惊讶/中性 |
| `dialect` | `dialect` | `cantonese` · `chuanyu dialect` |
| `ip` | `voice_id` | US_Emma, US_James, UK_George, UK_Charlotte (+ undeclared Chinese ids) |
| `voice_design` | `instruct` (voice description) | — |
| `freeform` | `instruct` (required) | — |

Language lives in `options.language` (or top-level `language`) and accepts
`zh`, `en`, `ja`, `ko`, `de`, `fr`, `es` — short codes and full names both resolve.

## Critical gotchas

1. **The umbrella gateway id is not the model.** Send `ming-tts`; a gateway
   alias such as `audio` typically fails with `unknown model id`.
2. **Controls go in the nested `options` object.** Unknown keys return HTTP 500
   with a list of supported options.
3. **Use `instruct`, not `instructions`.** Top-level `instructions` maps to an
   option named `instruction`, which Ming does not accept (`500 unknown Ming TTS
   request option: instruction`). Top-level `instruct` and `options.instruct` work.
4. **Top-level `speed` is rejected** (`500 Ming TTS does not accept structured
   controls`) — Ming's speed is the categorical `options.speed` on the `basic` template.
5. **Values are not validated.** Unknown `emotion`/`voice_id` strings are passed
   through (garbage in → garbage out). Use the exact vocabularies.
6. **`basic` does not enforce all three attributes** in tested builds; omitting one
   produced 30 s of bad audio. Always send `speed` + `pitch` + `volume`.
7. **`freeform` requires `instruct`** (`500 Ming freeform requires instruct`).
8. **A reference transcript matters.** `voice_ref` + a wrong `reference_text`
   produced 13.6 s of garbage for a 4-word input; with the matching transcript the
   output matched the library voice byte-for-byte. A `voice` library name may
   auto-inject its transcript.
9. **Streaming is usually unavailable.** The model entry is typically
   `mode: offline`; `response_format: pcm` can be rejected by the server frontend.
   `wav` (default), `mp3`, and `json` are the safe formats.
10. **First request after an idle unload is slow** (model reload); retries are warm.
11. **Option support varies by audio.cpp build.** Newer options
    (`export_speaker_embedding_file`, `stream_frames_per_event`) may be missing;
    an unknown option returns a 500 listing what the build supports.
12. **Empty/whitespace text** → `400 Ming TTS requires text input` / `400 Ming
    generated no audio; check the text and max_tokens`.

## Files

- `scripts/ming_tts.py` — request builder (stdlib only; reads `MING_TTS_BASE_URL` / `MING_TTS_API_KEY`).
- `scripts/generate.sh` — shim to the above.
- `patterns/generate-speech.md` — the main workflow, formats, long text, errors.
- `patterns/control-speech.md` — control templates and paralinguistic tags.
- `patterns/clone-and-design.md` — cloning, library voices, voice design, freeform.
- `references/wire-api.md` — exact fields, full options table, error catalog.
- `references/voice-catalog.md` — voice ids and control vocabularies.
- `references/upstream-contract.md` — the Python 0.5B contract and internals.
