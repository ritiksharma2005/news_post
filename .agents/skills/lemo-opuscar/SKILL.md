---
name: lemo-opuscar
description: Direct and produce a short film made entirely in code, in one of the styles of the Lemo-Opuscar library (e.g. Impasto Oil Painting 油画厚涂, Watercolor Brush 水彩笔刷, Ukiyo-e 浮世绘, Satellite Briefing 卫星简报, Exploded Teardown 产品拆解). Use when the user asks for a video, film, short, promo, explainer or animation (视频、短片、动画、宣传片) in a named style, including explainers built from real material such as satellite imagery, laser scans, CAD files or archive scans (数据解说、科普、产品拆解), and new films cut from real archive footage and documents (剪辑纪实, e.g. 用档案影像剪一支新闻片); when they want a film about their own topic and haven't chosen a style (help them choose); when they want to change a style into their own, make their own style from a blank page, or use a style they saved (改风格、从空白开始、我的风格); when they start the skill without saying what they want; or when they ask which film styles there are. Not for plain editing, trimming or converting the user's existing video files.
---

# Lemo-Opuscar

The styles, guides and tools live in the Lemo-Opuscar library ([github.com/lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)). The library is cloned locally at `~/lemo-opuscar` (and also available in `/Users/ritiksharma_2005/CODE 🧑‍💻/lemo-opuscar`).

## Setup and Quickstart

1. **Verify the library**: Run [setup.sh](./scripts/setup.sh):
   ```sh
   sh scripts/setup.sh
   ```
   It confirms the library at `~/lemo-opuscar`, checks system tools (Node, ffmpeg, Python), and exports `LIB=<path>`.

2. **Install core tools**:
   ```sh
   sh scripts/setup.sh deps
   ```
   Add `deps voice` or `deps music` later if needed ([TECHNIQUE.md](./references/TECHNIQUE.md)).

3. **Follow the library**: Read [AGENTS.md](./references/AGENTS.md) and [DIRECTOR.md](./references/DIRECTOR.md) for step-by-step production (brief → treatment → style look → audio → motion → mix → delivery).

What changes in skill mode:

| | |
|---|---|
| Project folder | `<name>/` in the folder the user started from (lowercase letters, digits, hyphens; avoid `#` and `?` in the path). Wherever the guides say `films/<name>/`, read this folder |
| Running tools | from `$LIB`, with the project's absolute path: `cd "$LIB" && node core/render/still.mjs "<project>" 1.5 3` |
| Library files in pages | absolute URLs: `/core/lib.js`, `/node_modules/three/…` (the project is served at `/@film/`) |
| Library files in scripts and `build.sh` | `$LIB/…`, with `LIB=<path>` at the top of `build.sh`; never `../..` |
| Demo source | not downloaded. `sh scripts/setup.sh demo <slug>`, only after your `TREATMENT.md` is written, to read its techniques; it is not meant to be rendered. An Edit & Documentary style is the exception: fetch it before the treatment to use the material tools its `STYLE.md` names in `demo/tools/` (`$LIB/AGENTS.md`, "Treatment first") |

Deliver what `$LIB/DIRECTOR.md` §11 lists, in the project folder, and tell the user where it is.
