# Clone a voice, design a voice, freeform delivery

Three ways to choose *who* speaks. All go through the same endpoint; the
difference is which request fields carry the voice.

## 1. Zero-shot cloning (`voice_ref` / `voice`)

Give the server a reference recording (and, ideally, its transcript). The model
conditions on the pair; with no transcript it conditions on the speaker
embedding alone (weaker but usable).

### Request fields

| Field | Shape |
| :--- | :--- |
| `voice_ref` | server-local path (`/path/to/reference.wav`), `{"type":"path","path":...}`, or `{"type":"base64","data":"<b64 WAV>"}` (5 MiB limit; data URIs accepted) |
| `reference_text` | exact transcript of the recording (top-level or `options.reference_text`) |
| `voice` | name resolved server-side: a configured preset first, then a server voice library entry, else a model-native id |
| `options.use_speaker_embedding` | default `true`; `false` disables speaker conditioning (also disables a preset's) |
| `options.zero_speaker_embedding` | default `false`; `true` uses a zero speaker row instead of any reference |
| `options.speaker_embedding_file` | path (or list) to a 192-dim CAMPPlus embedding `.pt`/safetensors; supersedes reference audio |

Selection order when several are present: explicit `voice_ref` wins; then a
`voice` matching a configured preset; then a `voice` matching a library WAV;
otherwise `voice` is passed to the model as a native id. Prefer one method per
request.

### Server-side voice libraries

Some deployments configure a shared directory of reference recordings plus a
`prompt_text` mapping file (`<name>|<transcript>` per line). A request
`voice: "<name>"` then clones that recording without sending audio. List what a
deployment exposes with:

```
GET $MING_TTS_BASE_URL/audio/voices?model=ming-tts
```

Names depend entirely on the deployment; check before using one. Voices without
a transcript line still work as speaker-only conditioning.

### Inline reference audio

For a recording that exists only on the client side, send it inline; the script
base64-encodes local files automatically:

```
--input 'Cloned from an inline reference.' \
--voice-ref /path/to/reference.wav \
--reference-text 'exact transcript of the recording'
```

Server-side library paths pass through unchanged (the script treats `/voices/…`
as server-side by convention); everything else that exists locally is encoded.

### Gotchas

- **Wrong transcript → garbage.** Verified: a 4-word input with a mismatched
  `reference_text` produced 13.6 s of unusable audio; with the matching text it
  was clean and reproducible. If you do not know the transcript, omit
  `reference_text` (speaker-only) rather than guessing.
- `export_speaker_embedding_file` is missing from some builds;
  `speaker_embedding_file` is accepted.
- Reference encoding consumes RNG: the same request can differ across a fresh vs
  cached reference unless the seed and cache state match (`reference_cache`
  session option, default true).
- Upstream Python note: prompt audio alone is dropped if `prompt_text` is
  missing (the acoustic latent is unusable without it) — the runtime then falls
  back to speaker-only conditioning.
- Voice cloning is for consented/legitimate use; label synthetic speech where it
  could be mistaken for a real recording (see the upstream disclaimer).

## 2. Voice design (`template_name: voice_design`)

Describe the voice; no reference audio. The description goes in
`options.instruct` (upstream calls this control `style`). Three accepted forms:

1. **Structured attribute list** — e.g.
   `性别: 女童.\n\n音高: 清亮童声高音.\n\n语速: 节奏明快，富有活力.\n\n…`
2. **Free-form natural language** — e.g.
   `成熟沉稳的男性纪录片旁白，吐字清晰，节奏舒缓。`
3. **Role-play prompt** — e.g. a palace-drama empress with calm authority.

```
--input 'Good evening. The harbor is quiet tonight.' \
--template-name voice_design \
--instruct 'A calm adult man with a clear, warm voice.' --language en
```

```
--input '冰川在漫长岁月中缓缓移动，留下深刻的痕迹。' \
--template-name voice_design \
--instruct '成熟沉稳的男性纪录片旁白，吐字清晰，节奏舒缓。' --language zh
```

`voice_design` text is not split the way plain TTS is (the style applies to the
whole utterance); multi-chunk runs cap at 120 codepoints and anchor later chunks
to the first generated chunk. Role-play descriptions are the weakest
voice-design sub-score upstream.

## 3. Freeform delivery (`template_name: freeform`)

A natural-language instruction about *delivery* (tone, pacing, character) rather
than a voice description. `options.instruct` is **required** (blank → 500
`Ming freeform requires instruct`). Do not combine with structured controls.

```
--input 'The old radio crackled softly as the storm moved across the valley.' \
--template-name freeform \
--instruct 'Speak in a warm, intimate storytelling voice, unhurried.' --language en
```

```
--input 'Keep your eyes forward and your shoulders relaxed. One more round—you can do this!' \
--template-name freeform \
--instruct 'Sound like an encouraging sports coach, energetic and firm without shouting.' --language en
```

The `tts` template also accepts a raw `instruct` (the spec calls it "raw
conditioning text for freeform or tts"); `freeform` is the same path with the
required-argument check. Reference-free generation is recommended for both;
adding a reference is possible but not the norm.

Exact upstream instruction examples (preserved verbatim):

| Scenario | Instruction |
| :--- | :--- |
| English: encouraging sports coach | `Sound like an encouraging sports coach, energetic and firm without shouting.` |
| English: warm storytelling | `Speak in a warm, intimate storytelling voice, unhurried.` |
| Chinese: gentle bedtime story | `用温柔、舒缓的声音讲述睡前故事，像在轻声安慰孩子。` |

## Upstream → wire mapping (cheat sheet)

| Upstream Python (`synthesize`) | Wire request |
| :--- | :--- |
| `task="TTS"`, `prompt_wav_path`, `prompt_text` | `voice_ref` + `reference_text` (or a `voice` library name) |
| `task="VOICE_DESIGN"`, `controls={"style": X}` | `options={"template_name":"voice_design","instruct":X}` |
| `task="FREEFORM"`, `instruction=X` | `options={"template_name":"freeform","instruct":X}` |
| `task="IP"`, `controls={"ip": X}` | `options={"template_name":"ip","voice_id":X}` |
| `task="EMOTION"`, `controls={"emotion": X}` | `options={"template_name":"emotion","emotion":X}` |
| `task="BASIC"`, `controls={"speed","pitch","volume"}` | `options={"template_name":"basic","speed","pitch","volume"}` |
| `task="DIALECT"`, `controls={"dialect": X}` | `options={"template_name":"dialect","dialect":X}` |
| `task="MULTILINGUAL"`, `language_id=X` | `options={"template_name":"multilingual","language":X}` |
| `use_spk_emb=True` | default when `voice_ref` is present |
| `use_zero_spk_emb=True` | `options.zero_speaker_embedding=true` (or an ip/voice_design/freeform template) |
| `cfg` / `sigma` / `temperature` | `options.guidance_scale` / `sigma` / `temperature` |
| `max_length` | `options.text_chunk_size` (or `raw_text`) |
| `spk_emb_path` | `options.speaker_embedding_file` |
