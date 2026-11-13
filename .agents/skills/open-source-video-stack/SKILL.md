---
name: open-source-video-stack
description: Produce dynamic, high-engagement videos using the free, open-source video creation stack: HyperFrames (motion graphics & animated web layouts), FFmpeg (dynamic cuts & audio/video muxing), Whisper (word-level captions & speech alignment), and Edge-TTS (zero-cost neural voiceovers). Use when the user asks to build motion graphics videos, viral edits, explainers, or reels combining HTML/CSS animations with automated voiceover and dynamic subtitles.
---

# 🚀 Open-Source Video Creation Stack

A 100% free, open-source, deterministic pipeline for creating viral motion graphics and broadcast reels using:

```text
┌─────────────────┐       ┌─────────────────┐
│   🎙️ Edge-TTS   │       │   💬 Whisper    │
│  Neural Voice   │ ────> │ Word Timestamps │
└────────┬────────┘       └────────┬────────┘
         │                         │
         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐
│ 🎬 HyperFrames  │       │    ✂️ FFmpeg    │
│ Motion Graphics │ ────> │  Dynamic Cuts   │ ───> 📱 Master MP4 Video
│   (HTML/GSAP)   │       │  Audio Mixing   │
└─────────────────┘       └─────────────────┘
```

---

## 1. The Four Core Pillars

### 🎬 1. HyperFrames (`motion graphics`)
- **Repository**: [`heygen-com/hyperframes`](https://github.com/heygen-com/hyperframes) (Local copy: `CODE 🧑‍💻/hyperframes`)
- **Purpose**: Programmatic HTML5, CSS3, and GSAP timeline animations rendered frame-by-frame to deterministic video.
- **Components**:
  - Broadcast lower-third straps
  - Dynamic profile cards & metric counters
  - Kinetic headline slams & wipes
  - Interactive Like & Follow animated CTA buttons
- **CLI Commands**:
  ```bash
  npx hyperframes init my-project
  npx hyperframes preview   # Live browser preview with hot reload
  npx hyperframes render    # Deterministic frame-by-frame MP4 render
  ```

### ✂️ 2. FFmpeg (`dynamic cuts`)
- **Purpose**: High-performance multi-track assembly, frame-accurate scene cuts, audio ducking, and hardware-accelerated H.264 encoding.
- **Key Capabilities**:
  - 120 BPM tempo-synchronized scene transitions
  - Multi-layer audio mixing (Voiceover at 100%, BGM bed at -20 dB)
  - Subtitle styling and burning (`libass` filter)
  - Seamless concat and color gradient mapping

### 💬 3. Whisper (`captions`)
- **Purpose**: Word-level acoustic alignment and transcription for punchy mobile subtitles.
- **Workflow**:
  - Ingests generated voiceover audio
  - Extracts millisecond-accurate word boundaries
  - Formats into 2–4 word subtitle chunks with keyword highlights (`#FFC21A` amber box)
  - Emits `.srt` or `.ass` for FFmpeg burning or HyperFrames DOM captions

### 🎙️ 4. Edge-TTS (`voiceover`)
- **Purpose**: Expressive, free neural speech synthesis without API keys or usage fees.
- **Recommended Voices for Campus & Indian News**:
  - `en-IN-PrabhatNeural` (Authoritative, natural male broadcast voice)
  - `en-IN-NeerjaNeural` (Warm, professional female broadcast voice)
- **Features**: Pitch and rate adjustments, natural sentence boundaries.

---

## 2. Standard Production Workflow

```bash
# Step 1: Synthesize Voiceover with Edge-TTS
python3 -c "
import asyncio, edge_tts
communicate = edge_tts.Communicate('Your script here', 'en-IN-PrabhatNeural', rate='+12%')
asyncio.run(communicate.save('voice.mp3'))
"

# Step 2: Generate Word-Level Captions with Whisper / Faster-Whisper
python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('base', device='cpu', compute_type='int8')
segments, info = model.transcribe('voice.mp3', word_timestamps=True)
# Export to SRT with word boundaries
"

# Step 3: Animate Motion Graphics with HyperFrames
# Write or customize scene compositions in HTML/CSS/GSAP
npx hyperframes render --composition=main --output=graphics.mp4

# Step 4: Final Mix & Dynamic Cuts with FFmpeg
ffmpeg -y -i graphics.mp4 -i voice.mp3 -i bgm.wav \
  -filter_complex '[1:a]volume=1.0[v];[2:a]volume=0.18[bg];[v][bg]amix=inputs=2:duration=first[aout]' \
  -map 0:v -map '[aout]' -c:v libx264 -pix_fmt yuv420p -shortest master_reel.mp4
```

---

## 3. Related Installed Skills
- **`hyperframes`**: Core HTML/CSS/GSAP motion graphics engine ([SKILL.md](../hyperframes/SKILL.md))
- **`hyperframes-cli`**: CLI commands and flags ([SKILL.md](../hyperframes-cli/SKILL.md))
- **`hyperframes-registry`**: Reusable video components ([SKILL.md](../hyperframes-registry/SKILL.md))
- **`media-use`**: Presets for voice, audio, and presenters ([SKILL.md](../media-use/SKILL.md))
- **`news-video-generator`**: NEWS NIT IIT vertical video pipeline ([SKILL.md](../news-video-generator/SKILL.md))
