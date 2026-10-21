# FrameFlow Studio — Windows 11 prototype

Version: 0.6.0

## Run from source
1. Install Python 3.11+ and enable "Add Python to PATH".
2. Install FFmpeg (including ffprobe) and add its `bin` folder to PATH when running from source.
3. Run `START_FRAMEFLOW.bat`.

## Current functionality
- Local video and still-photo import; photos become five-second slideshow segments.
- Heuristic scene-change detection, sharpness ranking, and a lightweight face-presence bonus for videos. Face detection does not identify people or distinguish the couple.
- Target duration planning and FFmpeg MP4 export at 1080p or 4K, with four quality presets.
- Save and reopen project settings as JSON.
- Release-page update check inside the app.
- Aspect ratio and basic color looks.
- Original audio can be retained, muted, or lowered under optional background music.
- Media is processed locally; original source files are not deleted.

## Build
GitHub Actions runs a Windows build on pushes to `main`, checks Python syntax, and packages the executable with FFmpeg/FFprobe in a ZIP workflow artifact. The generated package should not be considered verified until the workflow succeeds and the ZIP is tested on a Windows PC. This is not yet a signed installer or automatic updater.

## Important limitations
This is an early functional prototype, not a finished professional editor. Scene detection and sharpness ranking are heuristics, not semantic understanding of wedding events. Bride/groom identification, face tracking, event recognition, photo motion/ken-burns, transitions, logo overlays, batch exports, automatic update installation, and a signed installer are not implemented yet. Test on copies before using for paid client work.
