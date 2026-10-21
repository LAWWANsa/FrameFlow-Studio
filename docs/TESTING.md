# Export test checklist

Run tests using copies of media, not the only originals.

- [ ] MP4 with source audio, no music: output should retain source audio.
- [ ] MP4 without audio, with music: output should contain music.
- [ ] Mixed input clips with and without audio: export should complete.
- [ ] Original audio muted with music: only music should be audible.
- [ ] Original audio ducked with music: source should remain audible under music.
- [ ] Test each aspect ratio and look.
- [ ] Test source duration shorter than requested target.
- [ ] Test paths containing Arabic characters and spaces.
- [ ] Verify output plays and duration is close to target.

The repository's automated Windows workflow currently checks Python syntax and packages an executable. It does not replace real media playback tests.
