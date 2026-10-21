# FrameFlow Studio — Windows 11 prototype

## Run from source
1. Install Python 3.11+ and enable "Add Python to PATH".
2. Install FFmpeg (including ffprobe) and add its `bin` folder to PATH.
3. Run `START_FRAMEFLOW.bat`.

## Current functionality
- Local video import, heuristic scene-change detection and basic sharpness ranking.
- Target duration planning and FFmpeg MP4 export.
- Aspect ratio and basic color looks.
- Original audio can be retained, muted, or lowered under optional background music.
- Media is processed locally; original source files are not deleted.

## Build
GitHub Actions now runs a Windows build on pushes to `main`, checks Python syntax, and uploads a Windows executable ZIP as a workflow artifact. This is a CI artifact, not yet a signed installer or automatic updater.

## Important limitations
This is an early functional prototype, not a finished professional editor. Scene detection and sharpness ranking are heuristics, not semantic understanding of wedding events. Advanced face tracking, event recognition, photo motion, transitions, logo overlays, batch projects, automatic update installation, and signed installer are not implemented yet. Test on copies before using for paid client work.
