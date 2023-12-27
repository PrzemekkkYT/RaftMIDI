# RaftMIDI
RaftMIDI let's you translate a lot of (unfortunately not all) MIDI files to AutoHotkey keystrokes to play piano in the game Raft automatically<br>
Also includes MIDI track selection for (theoretically) better results

# Usage
- Run midiraft.py using at least python 3.8
- Input local path to file (like ./RushE.mid)
- Input what tracks from file to use and separate them using commas (like 3, 5, 6)<br>You can also just type -1 to use all of available tracks (which may or may not sound good, depends on song)
- Run exported .ahk file, on Raft press ALT+C to start playing, and hold F1 to stop

# Error Description
- ValidationError - MIDI just can't be converted, you need to find another one if you want to use this song
- TrackSelectionError - You may have input tracks wrongly
- PermissionError - You may have input path to file wrongly
- Any other error - If it doesn't convert the file, open an Issue on this repo or message me on Reddit
