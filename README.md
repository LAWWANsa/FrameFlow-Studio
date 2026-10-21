# FrameFlow Studio — Windows 11 prototype

## Run
1. Install Python 3.11+ from https://www.python.org/downloads/windows/ and enable "Add Python to PATH".
2. Install FFmpeg (including ffprobe) and add its `bin` folder to PATH.
3. Run `START_FRAMEFLOW.bat`. The launcher installs Python dependencies.

## Working in this milestone
- Local video import and target duration.
- Local scene-boundary candidates using OpenCV frame differences.
- Candidate ranking by a basic sharpness heuristic and chronological assembly.
- FFmpeg MP4 export, basic aspect ratio/color options, optional background music.
- Source files are not deleted and media is not uploaded.

## Important limitations
This is an early functional prototype, not a finished professional editor. The current renderer strips source audio from segments; when a music file is supplied it adds that music, otherwise the output is silent. Original-audio preservation/mixing must be implemented and tested next.
Scene detection and sharpness ranking are heuristics, not semantic understanding of wedding events. Face tracking, event recognition, photo motion, transitions, logo overlays, batch projects, update service and installer are not implemented yet.
Test on copies before using for paid client work.
