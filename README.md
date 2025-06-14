[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/przemekkk)

# RaftMIDI

RaftMIDI let's you translate a lot of (unfortunately not all) MIDI files to AutoHotkey keystrokes to play piano in the game Raft automatically<br>
Also includes MIDI track selection for (theoretically) better results
Don't be mad that some of the songs sound awful. It was and always will be problem with conversions

## Example:

- Ed Sheeran - Shape of You: https://www.youtube.com/watch?v=Emd-HqijJlE
- Andrew Wrangell - Rush E: https://www.youtube.com/watch?v=TxiLU1Cq6to

# Requirements

- At least python 3.8
- Python <b>[colored 1.4.4](https://pypi.org/project/colored/1.4.4/)</b> package | pip install colored==1.4.4
- Python <b>[py_midicsv 4.0](https://pypi.org/project/py-midicsv/4.0.0/)</b> package | pip install py_midicsv==4.0.0

# Usage

- Run midiraft.py using at least python 3.8
- Input path to file (Don't use quotation marks when file name has spaces, just paste it as is)
- Input what tracks from file to use and separate them using commas (like 3, 5, 6)<br>You can also just type -1 to use all of available tracks (which may or may not sound good, depends on song)
- Run exported .ahk file, on Raft press ALT+C to start playing, and hold F1 to stop

# Error Description

- ValidationError - MIDI just can't be converted, you need to find another one if you want to use this song
- TrackSelectionError - You may have input tracks wrongly
- PermissionError - You may have input path to file wrongly
- Any other error - If it doesn't convert the file, open an Issue on this repo or message me on Reddit
