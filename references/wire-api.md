# Wire API reference (`ming-tts`)

The request surface for Ming-3.0-tts-0.5B when served through the audio.cpp
implementation behind an OpenAI-compatible gateway (llama-swap). Sources: live
probing of a real deployment, the audio.cpp model spec
`model_specs/ming3_tts.json`, and `docs/models/ming3_tts.md` in the audio.cpp
project.

## How it is served

```
client → OpenAI-compatible gateway (llama-swap) → audio.cpp server → ming3_tts GGUF
```

- The model id is `ming-tts`; the gateway's umbrella/alias id (e.g. `audio`) is
  usually not a valid request `model`.
- The endpoint base URL is deployment-specific
  (`https://llama-swap.example.com/v1` in examples). Configure it with
  `MING_TTS_BASE_URL` / `--base-url`.
- Auth is a bearer API key (`MING_TTS_API_KEY`), supplied by the caller.
- Model options are validated against the build's embedded spec; option
  support varies by audio.cpp version.
- Some deployments mount a shared voice library (`voice_dir` + a `prompt_text`
  transcript mapping); names are deployment-specific. Check
  `GET /v1/audio/voices`.

## Endpoints reachable through the gateway

| Route | Purpose |
| :--- | :--- |
| `POST /v1/audio/speech` | speech generation (the main route) |
| `GET /v1/audio/voices?model=ming-tts` | list library/preset voice names |
| `POST /audioapi/v1/tasks/run` | audio.cpp-native generic request → JSON result |
| `GET /v1/models` | model catalog (+ loaded/unloaded status) |
| `GET /upstream/<model-id>/...` | direct pass-through to the audio.cpp server, when the gateway exposes it (e.g. `/upstream/ming-tts/v1/models?include_params=true`) |

## `POST /v1/audio/speech`

JSON body, `Authorization: Bearer $MING_TTS_API_KEY`,
`Content-Type: application/json`. Response `audio/wav` by default.

### Top-level fields

| Field | Type | Notes |
| :--- | :--- | :--- |
| `model` | string | `ming-tts` (required) |
| `input` | string | text to speak (required; empty → 400) |
| `options` | object | **all Ming controls live here** (table below) |
| `voice` | string | server-side name: configured preset → library WAV (with auto transcript) → model-native id |
| `voice_ref` | string \| object | server-local path, `{"type":"path","path":...}`, or `{"type":"base64","data":"<b64 or data URI>"}` (≤5 MiB) |
| `reference_text` | string | transcript of `voice_ref` (enables the acoustic prefix); also an option key |
| `language` | string | shortcut for `options.language` (the server uses it when the option is absent) |
| `instruct` | string | shortcut for `options.instruct` |
| `instructions` | string | **Ming does not support this** — maps to option `instruction` → 500 |
| `speed` / `speaking_rate` | number | **rejected** for Ming (`500 Ming TTS does not accept structured controls`) |
| `seed` | int or string | shortcut for `options.seed` (uint64 as string if > 2^53) |
| `max_tokens` | int | shortcut for `options.max_tokens` |
| `response_format` | `wav` \| `mp3` \| `json` \| `pcm` | `pcm` needs streaming support; `json` returns base64 WAV |
| `stream_format` | `sse` \| `audio` | requires a `mode: streaming` model entry; Ming is commonly offline |
| `busy_timeout_ms` | int | wait for the model lock (clamped by the model ceiling) |

### `options` (Ming 3.0 TTS 0.5B spec)

| Option | Type | Default | Values / notes |
| :--- | :--- | :--- | :--- |
| `template_name` | enum | `tts` on the tts route | `tts`, `multilingual`, `basic`, `emotion`, `dialect`, `ip`, `voice_design`, `freeform` |
| `language` | string | request's `language` | `zh`, `en`, `ja`, `ko`, `de`, `fr`, `es`; names resolve. Required by `multilingual`; ignored by `dialect` |
| `instruct` | string | — | voice description (`voice_design`) or raw conditioning text (`freeform`, `tts`). Required by `freeform` |
| `instruction_schema` | enum | `en` for dialect, else `zh` | `en`, `zh` (field names of the structured caption, not spoken language) |
| `speed` | enum | — | `慢速`, `中速`, `快速` (basic; categorical) |
| `pitch` | enum | — | `低`, `中`, `高` (basic) |
| `volume` | enum | — | `低`, `中`, `高` (basic) |
| `emotion` | string | — | `高兴`, `悲伤`, `愤怒`, `恐惧`, `厌恶`, `惊讶`, `中性` (emotion; unvalidated) |
| `dialect` | enum | — | `chuanyu dialect`, `cantonese` |
| `voice_id` | enum | — | declared: `US_Emma`, `US_James`, `UK_George`, `UK_Charlotte`; undeclared Chinese ids pass through |
| `reference_text` | string | — | transcript for `voice_ref`; without it, speaker-only conditioning |
| `speaker_embedding_file` | path_list | — | 192-dim CAMPPlus embedding (`[192]` or `[1,192]`); supersedes reference audio |
| `use_speaker_embedding` | bool | `true` | condition on the reference speaker embedding |
| `zero_speaker_embedding` | bool | `false` | zero speaker row instead of reference conditioning |
| `max_tokens` | int (min 1) | `1000` | max acoustic patches per chunk; also bounded by the 512-position context |
| `guidance_scale` | float | `2` | flow guidance |
| `sigma` | float (min 0) | `0.25` | flow SDE noise scale |
| `temperature` | float (min 0) | `0` | flow sampling temperature; zero still uses seeded noise |
| `seed` | int (min 0) | `1895` | reference-posterior + generation noise seed |
| `raw_text` | bool | `false` | one synthesis fragment, no frontend chunking |
| `text_chunk_size` | int (min 1) | 50 CJK-heavy / 300 otherwise; 120 for voice_design+freeform | chunk budget in Unicode codepoints |
| `text_chunk_mode` | enum | `tag_aware` | `default`, `tag_aware`, `japanese`, `endline` |
| `trim_silence` | bool | `true` | trim trailing low-energy 100 ms frames per fragment, keep 300 ms tail |

Some builds also expose `export_speaker_embedding_file`, `stream_frames_per_event`,
and `stream_chunk_policy`; older builds reject them as unknown options.

**Session option** (server config, not per request): `ming3_tts.reference_cache`
(default `true`) — reuse prepared conditioning for the most recently used
reference waveform.

### Response

| `response_format` | Content-Type | Body |
| :--- | :--- | :--- |
| omitted / `wav` | `audio/wav` | 16-bit PCM, 44100 Hz mono |
| `mp3` | `audio/mpeg` | if the server build includes the MP3 frontend |
| `json` | `application/json` | `{"audio":"<base64 WAV>","format":"wav","timing":{...}}` |

Headers on success: `x-audiocpp-audio-duration-ms`, `x-audiocpp-rtf`,
`x-audiocpp-wall-ms` (also present on mp3). `rtf` = inference wall time ÷ audio
duration.

### Error catalog (observed)

| Status | Message | Trigger |
| :--- | :--- | :--- |
| 500 | `unknown model id: <id>` | gateway umbrella id sent as `model` |
| 500 | `unknown Ming TTS request option: <name>. … Supported options: …` | unknown option key (also fires for `instruction`, and for options newer than the build) |
| 500 | `Ming TTS does not accept structured controls` | top-level `speed` (or a structured control outside `options`) |
| 500 | `Ming freeform requires instruct` | `template_name=freeform` without `instruct` |
| 500 | `failed to open safetensors file: <path>…` | `speaker_embedding_file` pointing at a missing/invalid file |
| 400 | `Ming TTS requires text input` | empty `input` |
| 400 | `Ming generated no audio; check the text and max_tokens` | whitespace-only / unspeakable text |
| 400 | `server frontend supports speech response_format=mp3; unsupported response_format=pcm` | `response_format: "pcm"` on an offline entry |
| 500 | `failed to parse json at byte 0` | multipart form-data instead of JSON |

### `POST /audioapi/v1/tasks/run` (audio.cpp-native)

Takes `{"model":"ming-tts","request":{...}}` where `request` uses the same
fields as the speech `options` (plus `text`, `voice_ref`, `reference_text`, …).
Returns JSON:

```json
{"audio":"<base64 WAV>","sample_rate":44100,"channels":1,
 "timing":{"wall_ms":648.2,"audio_duration_ms":2300,"rtf":0.282}}
```

Useful when a JSON result with timing is more convenient than response headers.

## Behavior verified on a live deployment

| Probe | Result |
| :--- | :--- |
| plain TTS `{"model":"ming-tts","input":...}` | 200, WAV 16-bit 44.1 kHz mono |
| `template_name` = emotion / basic / ip / dialect / multilingual | 200 each |
| library `voice` vs explicit `voice_ref`+matching `reference_text` | byte-identical outputs |
| `voice_ref` with mismatched transcript | 200 but 13.6 s of garbage for a 4-word input |
| base64 `voice_ref` (plain and data URI) | 200 each |
| undeclared Chinese `voice_id` | 200, audio differs from the English voices; fidelity unverified |
| invalid `emotion` value | 200, audio differs; unvalidated |
| `template_name=basic` missing pitch+volume | 200 but 30 s of bad audio for one line |
| top-level `instructions` | 500 `unknown … option: instruction` |
| top-level `instruct` | 200 |
| top-level `speed: 1.5` | 500 `does not accept structured controls` |
| `response_format: mp3` | 200 `audio/mpeg` |
| `response_format: pcm` + `stream_format: sse` | 400 frontend error |
| `seed` / `raw_text` / `text_chunk_size` / `trim_silence` | 200, output changes as expected |
| long paragraph chunked vs `raw_text` | 22.2 s vs 19.2 s (chunking active) |
| `GET /v1/audio/voices?model=ming-tts` | lists the deployment's library names |
| `GET /upstream/<id>/v1/models?include_params=true` | returns the build's full option table |
| `POST /audioapi/v1/tasks/run` | 200 JSON with audio + timing |
