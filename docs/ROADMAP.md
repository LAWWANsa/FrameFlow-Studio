# Roadmap

## Phase 0 — Repository and foundations
- Establish project structure and dependency policy.
- Keep media processing local.
- Clearly label incomplete features.

## Phase 1 — Functional local editing engine
- Discover FFmpeg and report clear setup errors.
- Read video duration, resolution, frame rate and audio streams.
- Detect scene boundaries locally with frame-difference/histogram methods.
- Score candidate segments using motion, sharpness and exposure heuristics.
- Plan a target-length edit without random cuts or overlapping source ranges.
- Render a real output with optional music, original-audio choice, fade and aspect-ratio handling.
- Show progress, elapsed time and cancellation.

## Phase 2 — Creative controls
- Styles, basic color treatment, gentle zoom/pan, photo motion and transitions.
- Chronological/creative sequencing and reusable presets.
- Logo overlay and alternate short-form export.

## Phase 3 — Optional local AI
- Local face detection/tracking and configurable priority subjects.
- Optional event/highlight classifiers only when a compatible model and hardware are available.
- Never imply that a heuristic is semantic understanding.

## Phase 4 — Reliability and distribution
- Test on varied real-world files including 4K and variable frame rate.
- Package for Windows 11, verify dependencies and failure handling.
- Release metadata and safe updater that checks signed/verified release assets.
- Preserve project settings and never delete original media.

## Release gate
A feature is complete only after a real test and a documented result. The application must not claim final/production-ready status before export and recovery paths are tested.
