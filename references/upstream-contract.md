# Upstream Ming-3.0-tts-0.5B contract and internals

Distilled from the upstream project (github.com/inclusionAI/Ming-3.0-tts,
MIT-licensed). The repo has **no serving code** — everything here is in-process
Python (`MingTTS.synthesize`). The OpenAI-compatible wire surface is an external
implementation of this contract; use `wire-api.md` for requests.

## Entry point

```python
MingTTS(model_path, device="cuda:0", text_normalization=True, cache_prompts=True)

model.synthesize(
    task, text,
    language_id=None, instruction=None, controls=None, instruction_schema=None,
    prompt_wav_path=None, prompt_text=None, spk_emb_path=None,
    use_spk_emb=False, use_zero_spk_emb=False,
    cfg=2.0, sigma=0.25, temperature=0.0,
    max_length=24, max_decode_steps=1000,
    trim_silence=True, raw_text=False, output_path=None,
) -> Tensor  # (1, samples), float
```

The request dict the engine consumes (`tts_tasks.build_task_generation_kwargs`)
has 12 keys: `prompt, text, use_spk_emb, use_zero_spk_emb, instruction,
prompt_wav_path, prompt_text, cfg, sigma, temperature, taskname, text_language`.

Generation defaults (`modeling_bailingmm.py`): `max_decode_steps=1000`,
`cfg=2.0`, `sigma=0.25`, `temperature=0`, `MAX_CACHE_LEN=512`.

## Task normalization and aliases

`task` is upper-cased, `-` → `_`, then mapped to a runtime task
(`tts_tasks._TASK_ALIASES`):

| Passed | Runtime task |
| :--- | :--- |
| `TTS`, `SEED`, `PLAIN`, `MULTILINGUAL`, `MULTILINGUAL_TTS` | `TTS` |
| `BASIC`, `EMOTION`, `DIALECT`, `IP` | same |
| `VOICE_DESIGN`, `STYLE`, **`FREEFORM`** | **`STYLE`** |

So `VOICE_DESIGN` and `FREEFORM` collapse to internal `STYLE`; `MULTILINGUAL`
is `TTS` + `language_id`. `taskname` in the request dict is the resolved value.

Validation rules (`build_task_generation_kwargs` / `build_task_instruction`):

- Non-structured tasks reject `controls`; structured tasks
  (`BASIC`/`DIALECT`/`EMOTION`/`VOICE_DESIGN`/`IP`) reject a raw `instruction`
  (they build their own caption).
- `FREEFORM` requires a non-empty `instruction` and rejects `controls`.
- `BASIC` requires all of `speed`, `pitch`, `volume`.
- `DIALECT` ignores `language_id`/`target_language` with a `UserWarning`.
- `MULTILINGUAL` requires `language_id`; `language_id` and `target_language`
  must not conflict.
- `use_spk_emb` and `use_zero_spk_emb` are mutually exclusive; `use_spk_emb`
  needs a prompt wav or a speaker-embedding path.

## Prompt and caption bytes (part of the trained protocol)

User-side prompt (`build_tts_prompt`):

```
Please generate speech based on the following description.
Please generate speech based on the following description.
Target language: Chinese.
```

(second line added when `language_id` is given; short codes and full names both
resolve; `yue`/`cantonese` → `Chinese`.)

Assistant-side structured caption (`build_structured_instruction`), field order
is trained:

- zh schema (default, except DIALECT): `序号, 说话人, 方言, 风格, 语速, 基频, 音量, 情感`,
  then `BGM`, then `IP`.
- en schema (DIALECT or `instruction_schema="en"`): `id, speaker, dialect, style,
  speed, pitch, volume, emotion`, then `BGM`, then `ip`.
- `BGM` is always `{"Genre","Mood","Instrument","Theme","ENV","SNR"}`, all `null`.
- Serialized as JSON (`ensure_ascii=False`), e.g.
  `{"audio_sequence": [{"序号": 1, "说话人": "speaker_1", ...}]}`.

## Token layout (`prompt_contract.py`, dense)

System prefix `<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n`,
user turn, assistant turn ending in `<|im_end|>`, then the audio start token.
Pinned IDs validated at load: `<|endoftext|>`=151643, `<|im_start|>`=151644,
`<|im_end|>`=151645, `<|vision_start|>`=151652, `<|vision_end|>`=151653,
`<|vision_pad|>`=151654, `<audioPatch>`=151705, `<audio>`=151706. Text-prefix
marker: ` Text input:\n`. Tokenizer mismatches **fail closed** (names alone are
not enough — IDs index embedding rows). Only the dense layout is implemented.

## Text frontend pipeline

`prepare_text` → strip Markdown (fenced/inline code, links, headings, `**bold**`)
→ optional TN → `add_period`. `split_text(max_length=24)` groups whole clauses
at punctuation and never cuts inside a clause; empty/unsynthesizable text raises.

- TN is bypassed for non-zh/en languages and for `DIALECT` — that is why
  Japanese kana survive.
- Paralinguistic tags are protected from TN verbatim (only surrounding text is
  normalized; boundary whitespace preserved).
- Text must yield at least one alphanumeric char or it errors.
- Trailing silence is trimmed **per fragment**, before fragments are joined.
- `raw_text=True` skips splitting + normalization (one piece) — how benchmarks
  were run.

## Voice conditioning internals

- **Speaker embedding:** CAM++ (`campplus.onnx`) via onnxruntime on **CPU**,
  Fbank 80-mel at 16 kHz → **192-dim**. `use_zero_spk_emb=True` substitutes a
  zeroed 192-dim vector.
- **Prompt latent:** the prompt waveform is encoded by the AudioVAE
  (`encode_prompt_latent`), which samples its posterior (consumes RNG).
- **Front padding, not back:** `_pad_prompt_waveform` pads the front because the
  tail of the prompt seeds the latent history for the first decode step.
- **Prompt cache:** keyed by the joined prompt path(s); `cache_prompts=True`
  by default.
- **Acoustic prompt needs its transcript:** `prompt_latent` is dropped when
  `prompt_text` is missing.
- **`spk_emb_path`:** `.pt` file; accepts a tensor or a dict with key
  `spk_emb`/`speaker_embedding`/`embedding`/`emb`; must be 192-dim.
- **Multi-fragment reference reuse:** for `STYLE` (VOICE_DESIGN/FREEFORM) with
  split text, the first generated fragment becomes the reference for later
  fragments; `use_zero_spk_emb` flips off afterwards.
- **Stop head:** generation stops when
  `stop_head(z_diff).softmax()[1] > 0.5 and step > 3`; budget is
  `(512 - prompt_len) // patch_size` latent steps.

## Audio I/O

- Prompt wav: stereo → mono (mean), resampled to 16 kHz for the speaker
  embedding and to the model sample rate for the latent.
- Output sample rate: **44100** (`config.audio_tokenizer_config.sample_rate`);
  `MingTTS.sample_rate` exposes it.
- Output is a float waveform `(1, samples)`; `output_path` writes via
  `torchaudio.save` (typically PCM16 WAV).
- Empty prompt audio → error.

## Environment / checkpoint / tooling

- 0.5b stack: `torch==2.6.0`, `torchaudio==2.6.0`,
  **`transformers==4.46.3`** (hard pin), `accelerate==1.3.0`,
  `x_transformers==2.9.2`, `diffusers==0.33.0`, `onnxruntime`,
  `soundfile==0.12.1`, `inflect`, `einops`, `loguru`.
- Docker: `pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime`, Python 3.11,
  `TORCH_CUDA_ARCH_LIST="8.0;9.0"`. Tested on H800-80GB and H20-96G.
- `flash-attn` optional (SDPA fallback; the config loader rewrites
  `flash_attention_2` pins to `sdpa` when absent).
- Text normalization needs `pynini==2.1.6`, loaded lazily; skip with
  `text_normalization=False` / `--no_text_normalization`.
- Checkpoint is self-contained (`model_type: dense`): `config.json`,
  `model.safetensors` (backbone + VAE + DiT + aggregator), `campplus.onnx`,
  tokenizer files. Download:
  `hf download inclusionAI/Ming-3.0-tts-0.5b --local-dir …`.
- Preflight (CPU-only, seconds): `python tools/preflight.py --model_path …` —
  checks files, dense model type, sample rate, tokenizer contract; warns on
  missing `pynini`/`flash_attn`.

## Data & assets in the repo

- `data/voice_presets/voice_prompts.json`: `DB30` (`感谢你的认可。`) and
  `lingguang` (`诶，你今天有空吗？我们能不能聊聊这件事啊？`) with wavs under
  `voice_audio/`.
- Ready-made prompt wavs: `data/wavs/emotion_prompt.wav` (emotion),
  `data/wavs/yue_prompt.wav` (Cantonese).
- Emotion/Dialect take a reference **wav only** (no transcript) upstream,
  because those tasks set `prompt_text_mode="none"`.

## Fine-tuning (0.5B)

- Data: UTF-8 JSONL, one sample per line, e.g.
  `{"audio":"wavs/001.wav","text":"...","language":"Chinese","task":"emotion","controls":{"emotion":"高兴"}}`.
  `audio` is relative to the JSONL; `controls` sit beside `task`/`text`.
- The script serializes `controls` into the assistant-side caption before the
  audio tokens; never hand-assemble special tokens or put control JSON in `text`.
- Flow: `python -m sft.prepare … --cache_speakers` → edit the full or LoRA
  config → `python -m sft.train --config …` (multi-GPU via `torchrun`,
  `--resume latest`) → `python -m sft.export --checkpoint … --output …`
  (LoRA merged on export). Install `requirements-sft.txt`.

## Limitations, license, disclaimer

- License: MIT. `LEGAL.md`: Chinese comments are the governing version.
- Usage: label synthetic speech as synthetic; no impersonation without consent;
  authors accept no liability.
- Known 0.5b limitations: weaker speaker similarity on the five new languages
  and Cantonese; multi-tag lines trail single-tag; emotion from delivery alone
  is weak; pitch is the weakest attribute; role-play voice design is the
  weakest sub-score; Korean CER (1.728%) trails German/Spanish.
- Leaderboards (Artificial Analysis, Oct 2026): 1st open-weights Controlled
  Voice; 1st overall Pronunciation Robustness (93.2%). Architecture: LM + DiT
  patch head + audio tokenizer.

## Upstream repository map

| Area | Files |
| :--- | :--- |
| High-level API | `ming_tts.py` (`MingTTS`) |
| Model | `modeling_bailingmm.py`, `configuration_bailingmm.py` |
| Task/controls contract | `tts_tasks.py` |
| Token/prompt layout | `prompt_contract.py` |
| Text frontend | `frontend/text_processing.py`, `toolkit.py`, `text_segment_cut.py`, `audio_processing.py` |
| Speaker embedding | `spkemb_extractor.py` (CAM++) |
| CLI | `infer.py` |
| Preflight | `tools/preflight.py` |
| Fine-tuning | `sft/README.md` |
| Docs / examples | `README.md`, `cookbooks/*` |
| Env / license | `requirements.txt`, `LICENSE`, `LEGAL.md` |
