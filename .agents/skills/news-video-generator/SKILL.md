---
name: news-video-generator
description: Produce 30-45 second vertical (9:16) broadcast news videos for NEWS NIT IIT (@news.nit_iit). Integrates multimodal Gemini 2.0 Flash scriptwriting, Edge-TTS Indian English voice performance, Lemo-Opuscar broadcast package graphics (animated lower-third strap, channel bug, slam captions with keyword highlight, split screens, push-in zoom), animated anchor presence, and Telegram approval before Instagram Reels publishing.
---

# NEWS NIT IIT — AI News Anchor Video Generator

This skill directs and produces 30–45 second vertical (9:16) broadcast news videos for **NEWS NIT IIT** (`@news.nit_iit`).

It synthesizes:
1. **Multimodal Gemini 2.0 Flash Scriptwriting**: Analyzes both the news graphic poster and caption to write a compelling 5-part broadcast narrative.
2. **Audio Performance**: High-energy Indian English voice (`en-IN-PrabhatNeural`, +12% rate, -2Hz pitch) mixed with a 112 BPM news ticker ambient bed.
3. **Lemo-Opuscar Broadcast Graphics**: Television news package elements inspired by `lemo-opuscar/styles/news-package` and `caption-news` (channel bug, lower-third animated strap, slam captions with yellow keyword block, document zoom, 120 BPM cut grid).
4. **Anchor Presence**: Branded studio anchor (white scarf, sunglasses, black jacket, NEWS NIT IIT desk) with dynamic body motion and camera punch-ins.
5. **Telegram Review & Approval Gate**: Finished video delivered to Telegram with interactive action buttons prior to publishing.
6. **Cloud-Only Execution**: Runs on GitHub Actions / cloud runners with zero local GPU load and zero cost.

---

## 1. Visual & Editorial Blueprint

### 5-Step Visual Sequence (30–45s)
| Beat | Duration | Visual Description | Audio / Voice |
|---|---|---|---|
| **1. Hook** | 0–5 s | Anchor in studio; camera punches in (1.0x → 1.15x); dynamic title slam with sound sting | High-energy question or shocking fact |
| **2. Reveal** | 5–15 s | Framed news poster / infographic with glowing HUD borders, category tab & date badge | Explains the core development |
| **3. Deep Dive** | 15–27 s | Detail push-in (1.05x), highlight boxes sweep over key metrics/companies; pause-to-read badge | Breaks down names, sectors, or evidence |
| **4. Bigger Picture**| 27–35 s | Return to anchor; lower-third strap flips to takeaway headline | Why this matters for campus and nation |
| **5. Outro** | 35–40 s | NEWS NIT IIT branded end-plate, social handle `@news.nit_iit`, follow CTA | Channel signature sign-off |

### Strict Pronunciation & Word Rules
> [!IMPORTANT]
> - **NIT & IIT Pronunciation**: When naming the channel, **ALWAYS** spell out letter-by-letter: `"N - I - T"` and `"I - I - T"`. Never pronounce as words (*"Nit"* or *"Eet"*).
> - **Signature Outro**: Must conclude with:
>   `"This is News N - I - T, I - I - T — your campus, our news."`
> - **Length**: 65–95 spoken words maximum to maintain 30–45s fast-paced delivery.

---

## 2. Broadcast Graphics System (Lemo-Opuscar Engine)

Refer to [Broadcast Graphics Guide](./references/BROADCAST_GRAPHICS_GUIDE.md) and [Lemo-Opuscar styles](../../lemo-opuscar/SKILL.md):
- **Channel Bug**: Top-right corner tag (`NEWS NIT IIT` plate + `AI NEWS` indicator).
- **Lower-Third Strap**: Positioned at bottom safe zone with category tab (`STARTUP`, `PLACEMENTS`, `RESEARCH`) and animated vertical headline flip.
- **Kinetic Slam Captions**: Center-bottom, max 2 lines, keyword highlighted in amber block (`#FFC21A`).
- **Timing Grid**: Hard cuts aligned with 120 BPM half-beat grid (0.5s increments).

---

## 3. How to Execute

### Option A: Local Test / Dry Run (Workspace)
From the project root (`/Users/ritiksharma_2005/CODE 🧑‍💻/news_post`):
```bash
# 1. Test script generation from post URL
python3 news_anchor_ai/ai/script_generator.py

# 2. Render anchor test scene
python3 news_anchor_ai/video/renderer.py

# 3. Run end-to-end pipeline with Job ID
python3 -m news_anchor_ai.main --source instagram --url "<INSTAGRAM_POST_URL>"
```

### Option B: Trigger Cloud Video Pipeline (Zero-Cost / Cloud-Only)
The production pipeline runs on GitHub Actions without consuming laptop resources:
```bash
# Trigger via GitHub Actions CLI
gh workflow run ai_news_anchor.yml -f post_url="<INSTAGRAM_POST_URL>"
```
The workflow will:
1. Ingest post & extract visual graphic.
2. Generate broadcast script via Gemini 2.0 Flash.
3. Synthesize voice & 112 BPM ambient bed.
4. Composite 9:16 broadcast video with animated graphics.
5. Send MP4 preview to your Telegram bot with:
   - `[APPROVE & PUBLISH]`
   - `[REGEN SCRIPT]`
   - `[REGEN VOICE]`
   - `[REJECT]`

---

## 4. Key Scripts & References
- **Script Generator**: `news_anchor_ai/ai/script_generator.py`
- **Video Renderer**: `news_anchor_ai/video/renderer.py`
- **Voice Generator**: `news_anchor_ai/voice/voice_generator.py`
- **Telegram Controller**: `news_anchor_ai/telegram/bot_controller.py`
- **GitHub Workflow**: `.github/workflows/ai_news_anchor.yml`
- **Lemo-Opuscar Library**: Located at `~/lemo-opuscar`
