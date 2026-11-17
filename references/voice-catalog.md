# Voice catalog and vocabularies

Voice ids and control values for Ming-3.0-tts-0.5B. The catalog below comes
from the upstream project's control reference
(`cookbooks/instruction_en.md`; the Chinese original `cookbooks/instructions.md`
governs). The audio.cpp runtime declares only the four English `ip` voices; the
Chinese catalog is accepted but undeclared (see `wire-api.md`).

## Server-side voice libraries

A deployment may expose a shared library of reference recordings plus a
`prompt_text` mapping (`<name>|<transcript>` per line). Select one with
`voice: "<name>"` and the server clones it, injecting the transcript when one is
listed. Names and contents are deployment-specific — discover them with
`GET /v1/audio/voices?model=ming-tts`. Voices without a transcript still work as
speaker-only conditioning.

## Built-in voices (`ip` / `voice_id`)

### Declared by the audio.cpp runtime (English)

| `voice_id` | Gender | Accent | Suits |
| :--- | :--- | :--- | :--- |
| `US_Emma` | female | American | assistants, narration, conversational product voice |
| `US_James` | male | American | narration, conversational (audio.cpp spec) |
| `UK_George` | male | British | audiobooks, formal announcements |
| `UK_Charlotte` | female | British | audiobooks, measured narration |

### Upstream Chinese voices without emotion variants

| ip | Gender | Age | Suggested roles | Voice description |
| :--- | :--- | :--- | :--- | :--- |
| `灵小安` | Female | Teenage girl | AI assistant; game guide; anime maid | Sweet, crisp, energetic, cute anime style |
| `灵语汐` | Female | Teenage girl | Playful younger sister; cheerful girl | Clear, bright, youthful, sunny |
| `灵小萌` | Female | Young adult | Audiobook narrator; soothing radio host | Bright, crisp, brisk, dependable |
| `灵小柔` | Female | Young adult | Customer-service assistant; IVR announcer | Clear, sweet, polite, patient, professional |
| `灵小雅` | Female | Young adult | Newsreader; audiobook presenter | Sweet, bright, youthful |
| `花小呗` | Female | Teenage girl | Customer-service agent; child character | Crisp, sweet, childlike, lively |
| `灵韵` | Female | Young adult | Customer-service agent | Bright, crisp, brisk, dependable |
| `妩媚妲己` | Female | Young adult | Alluring character | Sweet, crisp, light rising intonation, alluring |
| `灵婉` | Female | Teenage girl | Audiobook narrator | Clear, sweet, youthful, intimate, soothing |
| `灵小月` | Female | Young adult | Girl next door | Sweet, clear, energetic, welcoming |
| `灵朵儿` | Female | Young adult | Radio host; audiobook narrator; cultural narrator; mentor | Warm, thoughtful, unhurried, soothing |
| `灵小锋` | Male | Young adult | Caring boyfriend; dependable colleague; drama lead | Warm, resonant, confident, mature |
| `灵小川` | Male | Young adult | Radio host; food/fragrance reviewer; gentle partner | Warm, mellow, resonant, expressive |
| `灵小甄` | Female | Young adult | Livestream seller; fashion blogger | Bright, crisp, lively, persuasive |
| `灵小知` | Female | Young adult | Advertising voice; brand rep; sales adviser | Bright, confident, articulate, persuasive |
| `灵小惠` | Female | Young adult | Beauty-product livestream seller | Very fast, penetrating, urgent, enthusiastic |
| `灵小晴` | Female | Young adult | Livestream seller | Very fast, clear, powerful, bright |
| `灵小琪` | Male | Young adult | Food blogger; product reviewer; livestream seller | Sunny, friendly, natural, enthusiastic |
| `灵梦` | Female | Young adult | Affectionate girlfriend; dating-game character | Very sweet, youthful, playful |
| `灵恬` | Female | Young adult | Affectionate girlfriend; otome heroine | Honey-sweet, playful yet assured |
| `灵小汐` | Female | Young adult | Girl next door; first girlfriend; schoolmate | Clear, sweet, relaxed, innocent |
| `灵小棠` | Female | Young adult | Travel blogger; memoir narrator | Clear, warm, calm, experienced |
| `灵小梨` | Female | Young adult | Travel blogger; radio host; artistic young woman | Sweet, clear, playful, expressive |
| `灵小芸` | Female | Young adult | Radio host; close friend; podcast host | Warm, thoughtful, sincere, calm |
| `灵空` | Male | Young adult | Long-distance boyfriend; older caring companion | Low, resonant, close breathy, affectionate |
| `灵宇` | Male | Young adult | Otome lead; popular student; idol | Youthful, resonant, confident, teasing |
| `灵朗` | Male | Young adult | Ideal boyfriend; young executive; dating-game lead | Low, resonant, confident, affectionate |
| `灵楷` | Male | Young adult | Radio host; urban wanderer; documentary narrator | Warm, resonant, slow, soothing |
| `灵旭` | Male | Young adult | Student; young storyteller; late-night radio host | Clear, youthful, scholarly, calm |
| `灵江` | Male | Young adult | Radio host; memoir narrator; game-doc narrator | Warm, resonant, relaxed, heartfelt |
| `悲伤女声` | Female | Young adult | Urban professional; radio host; artistic vlogger | Gentle, determined, thoughtful, intimate |
| `皮六` | Male | Young adult | Advertising narrator; storyteller; confident protagonist | Bright, youthful, confident, dramatic |
| `悟空` | Male | Young adult | Storyteller; narrator; crosstalk performer | Expressive, theatrical, vivid exaggeration |

Character voices (metadata blank in the source): `蜡笔小新_野原美伢 (美伢)`,
`小猪佩奇_佩奇`, `康熙王朝_康熙`, `西游记_唐僧`, `甄嬛传_四郎`, `水浒传_武松`,
`水浒传_潘金莲`, `雍正王朝_雍正`.

### Upstream Chinese voices with emotion variants

Pass the full identifier as `voice_id` (Chinese base + `_` + Chinese emotion
suffix), e.g. `灵晓声_高兴`.

| Base voice | Gender | Age | Variants |
| :--- | :--- | :--- | :--- |
| 灵晓声 | Male | Young adult | 惊讶, 厌恶, 高兴, 中性, 悲伤 |
| 灵风信 | Female | Young adult | 生气, 中性, 厌恶, 高兴, 悲伤 |
| 灵惜梦 | Female | Young adult | 中性, 厌恶, 高兴, 悲伤, 恐惧, 惊讶, 生气 |
| 灵逸风 | Male | Young adult | 悲伤, 惊讶, 中性, 恐惧, 高兴 |
| 灵悦澜 | Female | Young/teenage | 中性, 高兴, 厌恶, 恐惧, 生气, 悲伤 |
| 灵御心 | Female | Young adult | 高兴, 中性, 生气 |
| 灵语恬 | Female | Young adult | 高兴, 恐惧, 悲伤, 惊讶, 生气, 中性 |
| 灵心恬 | Female | Young adult | 厌恶, 惊讶, 悲伤, 中性, 恐惧, 高兴, 生气 |
| 灵亦尘 | Male | Young adult | 中性, 恐惧 |
| 灵语尘 | Male | Young adult | 高兴, 厌恶, 惊讶, 中性, 悲伤, 恐惧 |
| 灵悦兮 | Female | Young adult | 高兴, 中性, 生气, 惊讶, 厌恶, 悲伤, 恐惧 |
| 灵若虚 | Female | Middle-aged/older | 惊讶, 中性, 悲伤, 高兴, 厌恶, 生气 |
| 灵未央 | Female | Young adult | 高兴, 中性, 惊讶, 悲伤, 恐惧, 生气 |
| 灵梦瑶 | Female | Child | 中性, 高兴, 悲伤, 惊讶, 生气 |
| 灵妙声 | Male | Adolescent | 中性, 悲伤 |
| 灵言澈 | Male | Young adult | 中性, 高兴 |
| 灵嘉肴 | Male | Young adult | 中性, 恐惧 |
| 灵孤影 | Male | Young adult | 中性 |
| 灵雨汐 | Female | Young adult | 中性, 恐惧, 高兴, 悲伤, 惊讶 |
| 灵信远 | Male | Young adult | 生气, 惊讶, 高兴, 恐惧, 悲伤 |
| 灵思齐 | Male | Young adult | 高兴, 恐惧, 厌恶, 惊讶, 悲伤 |
| 灵叙柔 | Female | Young–middle-aged | 高兴, 惊讶 |
| 灵绮木 | Female | Young–middle-aged | 厌恶, 高兴, 生气 |
| 灵渊霆 | Male | Middle-aged | 厌恶, 恐惧, 惊讶, 悲伤, 生气, 高兴 |
| 灵素心 | Female | Teenage girl | 悲伤, 厌恶 |
| 灵采薇 | Female | Young adult | 厌恶, 生气, 高兴 |
| 灵卓然 | Male | Young/middle-aged | 恐惧, 悲伤 |
| 灵浅忧 | Male (boy) | Child/adolescent | 高兴, 厌恶, 悲伤, 恐惧 |
| 灵昭野 | Male | Young adult | 高兴, 悲伤, 厌恶 |
| 灵心澜 | Female | Middle-aged | 高兴, 悲伤 |
| 灵犀言 | Male | Middle-aged/older | 悲伤, 生气 |
| 灵语冰 | Female | Young adult | 悲伤, 高兴, 惊讶 |
| 灵惊鸿 | Male | Young adult | 厌恶, 高兴, 惊讶, 生气, 悲伤 |
| 灵惜蕊 | Female | Young adult | 惊讶, 厌恶, 恐惧, 高兴, 悲伤, 生气 |
| 灵语萱 | Female | Young adult | 厌恶, 高兴, 恐惧, 生气, 悲伤 |
| 灵语烟 | Female | Teenage/young adult | 生气, 恐惧, 厌恶, 高兴, 悲伤 |
| 灵律雅 | Female | Middle-aged | 恐惧, 生气, 高兴 |
| 灵惊涛 | Male | Young adult | 恐惧 |
| 灵寒陌 | Male | Young adult | 厌恶, 高兴 |
| 灵决冥 | Male | Young adult | 厌恶, 生气, 恐惧 |
| 灵慈萱 | Female | Young adult | 生气, 悲伤, 恐惧 |
| 灵妙音 | Female | Young adult | 悲伤, 惊讶, 厌恶, 高兴, 恐惧 |
| 灵断尘 | Male | Young adult | 悲伤, 高兴, 惊讶, 恐惧, 厌恶 |
| 灵熙婉 | Female | Middle-aged | 高兴, 恐惧, 悲伤 |
| 灵旭扬 | Male | Young adult | 生气, 恐惧, 高兴, 惊讶, 悲伤, 厌恶 |
| 灵阅川 | Male | Young adult | 生气, 悲伤, 高兴, 厌恶, 恐惧 |
| 灵妩月 | Female | Young adult | 厌恶, 生气, 惊讶, 恐惧, 高兴, 悲伤 |
| 灵汐月 | Female | Young adult | 悲伤, 高兴 |
| 灵黛嗔 | Female | Young adult | 厌恶, 高兴 |

## Paralinguistic tags

Case-sensitive, brackets mandatory, inline anywhere (Chinese or English):

| Tag | Effect |
| :--- | :--- |
| `[Breathing]` | audible breath |
| `[Cough]` | cough |
| `[Sigh]` | sigh |
| `[Laughter]` | laughter |
| `[Uhm]` | hesitation filler |
| `[Surprise-ah]` / `[Surprise-oh]` | surprised "ah" / "oh" |
| `[Dissatisfaction-hnn]` | disgruntled "hnn" |
| `[Confirmation-en]` | affirming "en" |
| `[Question-ei]` / `[Question-ah]` / `[Question-en]` / `[Question-oh]` / `[Question-huh]` | questioning fillers |

## Language / value-language map

The API's control values are mostly Chinese, but several inputs are English.
English glosses in the docs are explanatory, **not** aliases.

| Input | Language of accepted values | Notes |
| :--- | :--- | :--- |
| Paralinguistic tags | English (fixed tokens) | case-sensitive, with brackets |
| `language` | English codes (`zh`, `en`, `ja`, `ko`, `de`, `fr`, `es`) | zh/en optional; other five required |
| `dialect` | English strings (`cantonese`, `chuanyu dialect`) | not selected via `language` |
| `emotion` | Chinese | 高兴 悲伤 愤怒 恐惧 厌恶 惊讶 中性 |
| `speed` | Chinese | 慢速 中速 快速 |
| `pitch` / `volume` | Chinese | 低 中 高 |
| `voice_id` | mostly Chinese names; 4 English | English: US_Emma, US_James, UK_George, UK_Charlotte |
| `instruct` (freeform/tts) | free natural language — English or Chinese | real English and Chinese examples |
| `instruct` (voice_design) | Chinese model input | structured list / free NL / role-play |
| `template_name` | UPPERCASE English | tts multilingual basic emotion dialect ip voice_design freeform |

## Task / reference matrix (upstream 0.5B)

| Task | Reference audio | Reference text | `language_id` | Controls |
| :--- | :--- | :--- | :--- | :--- |
| `TTS` | one | required | `zh`/`en` optional | — (inline tags allowed) |
| `MULTILINGUAL` | one | required | required: `de`/`es`/`fr`/`ko`/`ja` | — |
| `BASIC` | one | not accepted | — | `speed`, `pitch`, `volume` (all three) |
| `EMOTION` | one | not accepted | — | `emotion` |
| `DIALECT` | one | not accepted | — | `dialect` |
| `VOICE_DESIGN` | none | — | — | `style` |
| `IP` | none | — | optional | `ip` |
| `FREEFORM` | none (recommended) | — | optional | `instruction` (required) |

Upstream notes: `use_spk_emb=True` matches the reference recording;
`use_zero_spk_emb=True` is for reference-free tasks. `DIALECT` rejects/ignores
`language_id` (warns). `FREEFORM` cannot be combined with structured controls.
