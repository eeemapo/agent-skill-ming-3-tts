# Control speech (emotion, attributes, dialect, languages, voices, tags)

How to steer *how* the text is said. Every control is a key in the request's
`options` map. One template at a time: a structured template accepts only its
own controls; do not combine emotion with dialect, etc.

## Template selector

| Want | `template_name` | Keys to send |
| :--- | :--- | :--- |
| Plain speech (default) | omit or `tts` | — (optional `instruct`) |
| Emotion | `emotion` | `emotion` |
| Speed/pitch/volume | `basic` | `speed`, `pitch`, `volume` |
| Dialect | `dialect` | `dialect` |
| Another language | `multilingual` | `language` |
| Built-in voice | `ip` | `voice_id` |
| Voice description | `voice_design` | `instruct` |
| Delivery instruction | `freeform` | `instruct` |

`language` can also be sent top-level (`--language`); it resolves short codes and
full names (`zh`/`Chinese`, `ja`/`Japanese`, …).

## Emotion

Exact values (Chinese; the server does not validate, so an English gloss like
`happy` silently produces garbage):

`高兴` happy · `悲伤` sad · `愤怒` angry · `恐惧` fearful · `厌恶` disgusted ·
`惊讶` surprised · `中性` neutral

```
--input '所有的测试都通过了。' --template-name emotion --emotion 高兴 --language zh
```

Verified: 200 with 高兴 and 中性; an invalid `happy` was also accepted (different
audio) — treat undeclared values as unsupported.

## Basic attributes (speed / pitch / volume)

Categorical conditioning, not resampling. Exact values:

| Key | Values |
| :--- | :--- |
| `speed` | `慢速` slow · `中速` medium · `快速` fast |
| `pitch` | `低` low · `中` medium · `高` high |
| `volume` | `低` low · `中` medium · `高` high |

**Send all three.** Upstream Python requires the full triple; a tested runtime
accepted a partial request but generated 30 s of bad audio from a one-line
input. Do not omit one.

```
--input '今晚的观测将在云层散开后开始。' --template-name basic --speed 慢速 --pitch 中 --volume 高 --language zh
```

## Dialect

Exact values: `cantonese` (Cantonese) · `chuanyu dialect` (Sichuan–Chongqing).
This template takes no language; `language` is ignored (upstream warns).

```
--input '今日天气几好，我哋一齐去海边行下啦。' --template-name dialect --dialect cantonese
```

```
--input '今天天气巴适得很，我们一起出去转哈嘛。' --template-name dialect --dialect 'chuanyu dialect'
```

## Multilingual

`language` is **required** here for the five added languages. The voice is
carried by the reference recording (or the zero-speaker default), not by the
language — a Chinese reference can speak Japanese.

| Code | Language |
| :--- | :--- |
| `zh` | Chinese (works without `language`) |
| `en` | English (works without `language`) |
| `ja` | Japanese (required) |
| `ko` | Korean (required) |
| `de` | German (required) |
| `fr` | French (required) |
| `es` | Spanish (required) |

```
--input '오늘 저녁에는 비가 올 것 같아요.' --template-name multilingual --language ko
```

`yue` / `cantonese` resolve to Chinese (Cantonese is a dialect, not a target
language).

## Built-in voices (`ip` template)

The audio.cpp model spec declares four English voices:

| `voice_id` | Gender | Accent | Suits |
| :--- | :--- | :--- | :--- |
| `US_Emma` | female | American | assistants, narration, product voice |
| `US_James` | male | American | narration, conversational |
| `UK_George` | male | British | audiobooks, formal announcements |
| `UK_Charlotte` | female | British | audiobooks, measured narration |

```
--input 'The garden will remain open until sunset.' --template-name ip --voice-id US_Emma --language en
```

The upstream 0.5B catalog also has ~80 Chinese voices (`灵小柔`, `灵楷`, …).
The runtime **accepts** undeclared ids (a tested Chinese id returned 200 with
audio distinct from the English voices) but does not declare or validate them,
so fidelity is unverified — prefer the four declared voices unless the user asks
for a Chinese one. The full catalog is in `references/voice-catalog.md`.

## Paralinguistic tags

14 inline tags, **case-sensitive, brackets mandatory**, written anywhere in
Chinese or English text. They bypass normalization, so they reach the model
verbatim (the default `tag_aware` chunker keeps them intact):

`[Breathing]` `[Cough]` `[Sigh]` `[Laughter]` `[Uhm]` `[Surprise-ah]`
`[Surprise-oh]` `[Dissatisfaction-hnn]` `[Confirmation-en]` `[Question-ei]`
`[Question-ah]` `[Question-en]` `[Question-oh]` `[Question-huh]`

```
--input '[Sigh] I checked the drawer twice [Uhm] and it was empty again.' --language en
```

```
--input '[Laughter] 你居然真的把那封信藏在旧钟后面了。' --language zh
```

Tags compose mid-sentence. Verified: a line with two tags generated 3.9 s of
audio. Upstream notes that lines with many tags are less stable than
single-tag lines.

## Combining with a reference

Any of these templates can also take a reference voice (`--voice-ref` /
`--voice` / `--reference-text`) — see `clone-and-design.md`. Rules of thumb from
the upstream contract:

- Cloning/BASIC/EMOTION/DIALECT: condition on the reference speaker embedding
  (this is the default when `voice_ref` is present).
- `voice_design`/`freeform`/`ip`: reference-free generation is the norm; the
  instruction or voice id defines the voice.
- Do not combine `freeform`/`voice_design` with structured controls — pick one.

## What the server will not do

- Top-level `speed: 1.5` (OpenAI style) → `500 Ming TTS does not accept
  structured controls`.
- `options.instructions` / top-level `instructions` → `500 unknown Ming TTS
  request option: instruction`.
- `stream_format: sse` → only available when the model entry is `mode:
  streaming`; most Ming deployments are offline.
- Unknown enum values are **not** rejected; they degrade silently.
