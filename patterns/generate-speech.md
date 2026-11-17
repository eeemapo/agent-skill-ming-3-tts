# Generate speech (plain TTS)

The default workflow: turn text into audio with a `ming-tts` endpoint.
For emotion/dialect/voice controls see `control-speech.md`; for cloning and
voice design see `clone-and-design.md`.

## When to use

The user wants spoken audio from text: a clip, narration, announcement,
pronunciation sample, or a line to embed in something. No special voice or
control was requested.

## Steps

1. **Point at the endpoint and provide the key** (from your secrets manager,
   not committed anywhere):

   ```
   export MING_TTS_BASE_URL="https://llama-swap.example.com/v1"
   export MING_TTS_API_KEY="<your key>"
   ```

   In an agent harness, inject the key into the child environment instead of
   exporting it in a shell, so it never reaches logs or transcripts.

2. **Call the script:**

   ```
   python3 scripts/ming_tts.py \
     --input 'Welcome to the ming text-to-speech test.' \
     --language en --output ./out.wav
   ```

3. **Check the result.** The script prints the HTTP status, content type, byte
   count, and the `x-audiocpp-*` timing headers to stderr, then writes the WAV.
   `file out.wav` should say:
   `RIFF ... WAVE audio, Microsoft PCM, 16 bit, mono 44100 Hz`.

4. **Report the path** to the user and let them listen. There is no way to
   verify the voice by reading bytes; do not claim audio quality.

## Raw curl equivalent

The script is just a JSON POST. The same call by hand:

```
curl -sS -m 240 "$MING_TTS_BASE_URL/audio/speech" \
  -H "Authorization: Bearer $MING_TTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"ming-tts","input":"Hello.","options":{"language":"en"}}' \
  -o out.wav
```

**Gotchas:** use `/v1/audio/speech` (not `/v1/speech`); send JSON
(`Content-Type: application/json`), never multipart — form data returns
`500 failed to parse json at byte 0`; keep the key out of the transcript.

## Request anatomy

Top-level fields on `POST /v1/audio/speech` (everything else is model-specific
and belongs in `options`):

| Field | Meaning |
| :--- | :--- |
| `model` | `ming-tts` (required; gateway umbrella ids such as `audio` are usually rejected) |
| `input` | the text to speak (required; empty → 400) |
| `options` | object of Ming controls — see `references/wire-api.md` |
| `voice` | server-side voice name: a library entry or a configured preset |
| `voice_ref` | server-local WAV path, `{"type":"path",...}`, or `{"type":"base64","data":"..."}` |
| `reference_text` | transcript of `voice_ref`; enables the acoustic prefix (top-level or `options`) |
| `language` | target language (`zh en ja ko de fr es` or full names) — shortcut for `options.language` |
| `instruct` | voice description (voice_design) or raw delivery instruction (tts/freeform) — shortcut for `options.instruct` |
| `seed` | integer; default 1895 (also accepted in `options`) |
| `max_tokens` | max acoustic patches per chunk; default 1000 (also accepted in `options`) |
| `response_format` | `wav` (default), `mp3`, `json` (base64 WAV) |
| `busy_timeout_ms` | how long to wait for the model lock |

`instructions` (plural, OpenAI-style) does **not** work for Ming — it maps to an
unsupported option named `instruction`. Use `instruct`.

## Examples

English narration:

```
--input 'The garden will remain open until sunset, provided the weather stays clear.' --language en
```

Chinese:

```
--input '傍晚的风从山口吹过来，远处的云慢慢染成了金色。' --language zh
```

Deterministic repeat (fixed seed):

```
--input 'Good evening.' --language en --seed 7
```

The flow sampler remains stochastic at `temperature=0`; a fixed `seed` is what
makes runs reproducible (default seed 1895). `--guidance-scale` (default 2.0),
`--sigma` (0.25), and `--temperature` (0) map to the matching options.

## Long text

The server chunker splits text at sentence-ish boundaries before synthesis:

- Default budget: **50 codepoints** when hanzi/kana/Hangul outnumber letters and
  digits, otherwise **300**; **120** for `voice_design`/`freeform` (later chunks
  reuse the first generated chunk as their reference).
- `options.text_chunk_size` overrides the budget; smaller values insert more
  joins (and can sound choppier). Measured: a ~65-word paragraph took 22.2 s
  chunked vs 19.2 s with `raw_text=true`.
- `options.raw_text=true` sends the text as one fragment (no chunking) — used
  for benchmarks and when you want one continuous take.
- `options.text_chunk_mode`: `default`, `tag_aware` (default), `japanese`,
  `endline`.

The generation context is 512 positions shared by the prompt and the output
(one acoustic patch ≈ 80 ms). Long references or huge chunk budgets can starve
generation; reduce `text_chunk_size` or the reference length if audio cuts off.

## Output formats

| `response_format` | Response | Notes |
| :--- | :--- | :--- |
| omitted / `wav` | `audio/wav` | 16-bit PCM, 44100 Hz mono |
| `mp3` | `audio/mpeg` | only if the server build includes the MP3 frontend |
| `json` | `application/json` | `{"audio":"<base64 WAV>","format":"wav","timing":{...}}` |
| `pcm` | — | commonly rejected on offline model entries |

With `--output` the script writes the bytes and prints a summary; without it,
raw bytes go to stdout (pipe to a player/inspector, or redirect to a file).

Useful response headers for verification:

- `x-audiocpp-audio-duration-ms` — generated audio duration
- `x-audiocpp-rtf` — inference wall time ÷ audio duration (not wall-clock)
- `x-audiocpp-wall-ms` — inference wall time

## Troubleshooting

| Symptom | Cause / fix |
| :--- | :--- |
| `500 unknown model id: audio` | send `model: "ming-tts"`, not the gateway's umbrella id |
| `500 unknown Ming TTS request option: <name>` | typo or an option the build does not support; check `references/wire-api.md` |
| `500 Ming TTS does not accept structured controls` | top-level `speed` (or another structured control) sent outside `options` |
| `500 failed to parse json at byte 0` | multipart/form-data instead of JSON |
| `500 Ming freeform requires instruct` | `template_name=freeform` without `options.instruct` |
| `400 Ming TTS requires text input` | empty `input` |
| `400 Ming generated no audio; check the text and max_tokens` | whitespace-only/unspeakable text |
| 404 | wrong path (`/v1/speech` does not exist) |
| 401 | check the API key and that it belongs to this endpoint |
| First call slow (seconds) | model reload after idle unload; retry is warm |
| 503 / busy | another request holds the model lock; retry after the current generation |

## Notes

- `trim_silence` (default true) trims trailing low-energy 100 ms frames per
  fragment, keeping a 300 ms tail. Disable only if you need the raw tail.
- Reference encoding consumes RNG and new-vs-cached references consume different
  amounts of posterior noise — byte-identical repeats need the same seed *and*
  the same reference state (session option `reference_cache`, default true).
- `options.max_tokens` (default 1000) is a per-chunk cap; it is also bounded by
  the 512-position context.
- Available voice names depend on the deployment; list them with
  `GET /v1/audio/voices?model=ming-tts` where supported. See
  `references/voice-catalog.md`.
