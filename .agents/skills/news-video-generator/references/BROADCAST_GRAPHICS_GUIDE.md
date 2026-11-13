# Broadcast Graphics System for NEWS NIT IIT
Adapted from Lemo-Opuscar (`caption-news` & `news-package`)

This document defines the layout, color palette, typography, and motion rules for NEWS NIT IIT 9:16 vertical broadcast reels.

---

## 1. Frame Geometry (1080 × 1920 Vertical)

| Element | Coordinates / Bounds | Specs & Behavior |
|---|---|---|
| **Top Safe Zone** | y: 0 – 160 px | Retain clear for Instagram UI header |
| **Channel Bug** | Top right (x: 820, y: 120), w: 220, h: 56 | Gradient plate `#0A0D14` with white `NEWS NIT IIT` + red accent |
| **Category Tab** | Top left (x: 50, y: 120), h: 48 | Amber `#FFC21A` pill with dark uppercase tag (e.g., `STARTUP`) |
| **Content Stage** | x: 60 – 1020, y: 220 – 1500 | Anchor video or 9:16 framed news graphic with glowing border |
| **Lower-Third Strap**| x: 50 – 1030, y: 1540 – 1700 | Headline strap with vertical flip animation on story transitions |
| **Slam Captions** | Centered at y: 1420 – 1520 | 1–2 lines max, 48–56 px bold, yellow keyword box `#FFC21A` |
| **Bottom Safe Zone**| y: 1720 – 1920 px | Clear zone for Instagram captions, audio track name & actions |

---

## 2. Color System
- **Ink Background**: `#0A0D14` / `#121620` (Deep broadcast navy/black)
- **Primary Accent (Amber/Yellow)**: `#FFC21A` (Used for keyword callouts, category tabs, impact highlights)
- **Secondary Accent (Crimson Red)**: `#E63946` (Used for breaking news tag, alert borders, live markers)
- **Paper / Ivory Text**: `#F8F9FA` (Clean high-contrast readability)
- **Muted Subtext**: `#8D99AE` (Source credits, dates, timestamps)

---

## 3. Motion & Animation Rules (120 BPM Grid)
- **Pacing**: Every cut and transition happens on a 0.5s half-beat grid (120 BPM).
- **Camera Punch-In**:
  - Anchor opening: 1.0x → 1.15x push over 4 seconds.
  - News graphic reveal: 1.0x → 1.08x subtle continuous drift.
- **Slam Captions**:
  - Text enters in 2–3 word chunks with an overshoot scale (1.2x → 1.0x in 0.12s).
  - Crucial keywords wrapped in `#FFC21A` wipe box.
- **Graphic Pause-to-Read**:
  - High-density graphics (company logos, placement stats) display a pulsing "PAUSE TO READ" pill.
