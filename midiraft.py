from py_midicsv import midi_to_csv
from py_midicsv.midi.fileio import ValidationError
from colored import fg, attr

###############################################
# utils
###############################################


def pretty_traceback(error: BaseException, comment=""):
    file = error.__traceback__.tb_frame.f_code.co_filename
    line = error.__traceback__.tb_lineno
    # tb = "".join(traceback.format_exception_only(error))
    tb = str(error.__class__).replace("<class '", "").replace("'>", "")
    output = (
        f"{fg('red_1')}Error in {fg('red')}{file}{fg('red_1')} on line "
        f"{fg('red')}{line}{fg('red_1')}:\n  {tb}: {fg('red')}{error}{attr('reset')}"
    )
    if comment != "":
        output = (
            output
            + f"\n{fg('blue_1')}Additional comment: {fg('blue')}{comment}{attr('reset')}"
        )
    return output


def nearest_lower(lista, num):
    return min(list(lista), key=lambda x: abs(x - num) if x <= num else float("inf"))


def first_not_closed(lista, num):
    return next(
        (
            index
            for index, item in enumerate(lista)
            if len(item) == 2 and item[0] == num
        ),
        None,
    )


class TrackSelectionError(Exception): ...


###############################################
# main code
###############################################


def start():
    file_name = input("Enter a file path: ").replace("\\", "/")

    try:
        csv_string = midi_to_csv(f"{file_name}")
    except ValidationError as validError:
        print(
            pretty_traceback(
                validError,
                comment="Unfortunately, because of this error some midi songs can't be converted",
            )
        )
        exit(0)
    except Exception as exc:
        print(pretty_traceback(exc, comment="You may have entered the wrong path"))
        exit(0)

    print(
        f"Using {file_name} | Available tracks: {sorted(set([line[0] for line in csv_string if line[0] != '0']))}\n(track 1 is sometimes used only for initialization and doesn't contain any notes)"
    )

    try:
        try:
            track_num = [
                int(x)
                for x in input(
                    "Specify which tracks to include (-1 for all tracks): "
                ).split(",")
            ]
        except Exception:
            raise TrackSelectionError("Invalid track selection")
    except TrackSelectionError as exc:
        print(
            pretty_traceback(
                exc, "Tracks couldn't be acquired from input. Read README and try again"
            )
        )
        exit(0)

    return csv_string, track_num, file_name


# with open(f"{file_name}.csv", "w") as f:
#     f.writelines(csv_string)

notes_to_keys = {
    60: 1,
    62: 2,
    64: 3,
    65: 4,
    67: 5,
    69: 6,
    71: 7,
    72: 8,
    74: 9,
    76: 0,
    77: 4,
    79: 5,
    81: 6,
    83: 7,
    84: 8,
    86: 9,
    88: 0,
    48: 1,
    50: 2,
    52: 3,
    53: 4,
    55: 5,
    57: 6,
    59: 7,
}
notes_with_shift = [77, 79, 81, 83, 84, 86, 88]
notes_with_space = [48, 50, 52, 53, 55, 57, 59]


def get_timestamps(csv_string, track_num):
    ppq = 0
    # ticks/minute = bpm * ppq
    # ticks/second = bpm * ppq / 60
    # ticks/milisecond = bpm * ppq / 60_000
    tpms = {}
    timestamps = {}

    notes = []  # nuty wyciągnięte z pliku midi (nuta, start, koniec)

    off_notes = 0

    for line in csv_string:
        record = []
        for v in line.lower().replace("\n", "").split(", "):
            try:
                record.append(int(v))
            except:
                record.append(v)
        if record[2] == "header":
            ppq = record[5]
        if record[2] == "tempo":
            bpm = int(60_000_000 / int(record[3]))
            tpms[record[1]] = bpm * ppq / 60_000

        try:
            if record[0] in track_num or -1 in track_num:
                if record[2] == "note_on_c":
                    if record[5]:
                        note = record[4]
                        notes.append((note, record[1]))
                        timestamps[record[1]] = []
                        # print(f"{(note, record[1])=}")
                    else:
                        # to testuję
                        note = record[4]
                        if (index := first_not_closed(notes, note)) is not None:
                            if record[1] > notes[index][1]:
                                notes[index] = notes[index] + (record[1],)
                        # to jakoś działa
                        # notes[off_notes] = notes[off_notes] + (record[1],)
                        timestamps[record[1]] = []
                        off_notes += 1
                if record[2] == "note_off_c":
                    # to testuję
                    note = record[4]
                    if (index := first_not_closed(notes, note)) is not None:
                        if record[1] > notes[index][1]:
                            notes[index] = notes[index] + (record[1],)

                    # to jakoś działa
                    # notes[off_notes] = notes[off_notes] + (record[1],)
                    timestamps[record[1]] = []
                    off_notes += 1
        except Exception as exc:
            print(pretty_traceback(exc))
            # print(f"{record}")

    # print(len(timestamps))

    # print(notes)
    # for note in notes:  # populate timestamps with every timestamp used
    #     timestamps[note[1]] = []
    #     timestamps[note[2]] = []

    timestamps = {ts: [] for ts in sorted(timestamps)}

    notes = [note for note in notes if len(note) == 3]
    notes = [
        (min(notes_to_keys, key=lambda x: abs(x - note[0])), *note[1:])
        for note in notes
    ]

    for timestamp in timestamps:
        for note in notes:
            # print(f"{timestamp=} | {note=}")
            if note[1] == timestamp:
                timestamps[timestamp].append((note[0], "start"))
            elif note[2] == timestamp:
                timestamps[timestamp].append((note[0], "end"))

    timestamps = {
        key: sorted(value, key=lambda x: (x[1] == "start", x[1]))
        for key, value in timestamps.items()
    }

    return tpms, timestamps, notes


# print(f"{timestamps=}")
# print("====================================================================")
# print(f"{tpms=}")


def ahk(file_name, tpms, timestamps):
    with open(f"{file_name.split('/')[-1]}.ahk", "w+") as ahk:
        ahk.write("#Requires AutoHotkey v2.0\n\n")
        ahk.write("!c::{\n")

        for i, (_timestamp, _notes) in enumerate(timestamps.items()):
            ahk.write(
                f"sleep {(list(timestamps.keys())[i+1]-_timestamp)/tpms[nearest_lower(tpms.keys(), _timestamp)] if i<len(timestamps)-1 else 0}\n"
            )
            for note in _notes:
                if note[0] in notes_with_shift:
                    ahk.write('send "{shift down}"\n')
                elif note[0] in notes_with_space:
                    ahk.write('send "{space down}"\n')
                try:
                    ahk.write(
                        f'send "{{{notes_to_keys[note[0]]} {"down" if note[1]=="start" else "up"}}}"\n'
                    )
                except Exception as exc:
                    print(
                        pretty_traceback(
                            exc, comment="Problem with writing a send command to ahk"
                        )
                    )
                    # print(f"{i=} | {_timestamp=} | {_notes}")
                if note[0] in notes_with_shift:
                    ahk.write('send "{shift up}"\n')
                elif note[0] in notes_with_space:
                    ahk.write('send "{space up}"\n')

        ahk.write("}\n")
        ahk.write(
            'F1::{\nsend "{0 up}"\nsend "{1 up}"\nsend "{2 up}"\nsend "{3 up}"\nsend "{4 up}"\nsend "{5 up}"\nsend "{6 up}"\nsend "{7 up}"\nsend "{8 up}"\nsend "{9 up}"\nsend "{shift up}"\nsend "{space up}"\nExitApp\n}'
        )
        print("Converted successfully")


def notesheet(file_name, tpms, timestamps):
    with open(f"{file_name.split('/')[-1]}.notesheet", "w+") as notesheet:
        notesheet.write(
            "#File generated using https://github.com/PrzemekkkYT/RaftMIDI\n"
        )
        notesheet.write(f"{file_name.split('/')[-1]}|RaftMIDI|1.0\n")


if __name__ == "__main__":
    csv_string, track_num, file_name = start()
    export_type = input(
        "Do you want to export as .ahk or RandomThingsIveDone's Notesheet\nOptions: ahk | notesheet\n"
    )

    tpms, timestamps, notes = get_timestamps(csv_string, track_num)

    # print(f"{timestamps=}")
    print(f"{notes=}")
    print("====================================================================")
    print(f"{tpms=}")
    # print(f"{bpm=} | {ppq=} | t/s={bpm*ppq/60}")

    if export_type == "ahk":
        ahk(file_name, tpms, timestamps)
    elif export_type == "notesheet":
        notesheet(file_name, tpms, timestamps)
    else:
        print("No type selected. Conversion aborted.")
