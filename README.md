# FrameFlow Studio

Free, local-first video editing assistant for Windows 11, built for event and wedding footage.

## Principles
- Media stays on the user's computer; no cloud upload of footage or photos.
- No paid APIs or subscriptions.
- Open-source/local processing components only.
- Be honest about feature status: this repository is under active development and is not yet a complete editor.

## Planned milestones
1. Stable Windows desktop shell and project settings.
2. Local media probing and scene-boundary analysis.
3. Non-random highlight/shot selection with target-duration planning.
4. Local FFmpeg rendering, music/audio controls, aspect ratios and export presets.
5. Photo motion, logo overlay, color looks and reusable presets.
6. Optional local face/highlight models, subject priority, and short-form exports.
7. Versioned releases and a safe update checker.

## Development
Python 3.11+ is recommended. See `requirements.txt` and `docs/ROADMAP.md`.
The initial milestone must be tested on real sample footage before it is described as production-ready.
