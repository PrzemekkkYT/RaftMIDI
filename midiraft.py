import pathlib
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
    file_path = input("Enter a file path: ").replace("\\", "/")
    file_name = file_path.split("/")[-1].replace(".mid", "").replace(".midi", "")

    try:
        csv_string = midi_to_csv(f"{file_path}")
        with open("chuj.aaa", "w+") as aaa:
            for a in csv_string:
                aaa.write(f"{a}\n")
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

    return csv_string, track_num, file_path, file_name


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
    notes = sorted(notes, key=lambda x: x[1])

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
    with open(f"output/{file_name}.ahk", "w+") as ahk:
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


def notesheet_v1(file_name, tpms, notes):
    with open(f"output/{file_name}.notesheet", "w+") as notesheet:
        notesheet.write(
            "#File generated using https://github.com/PrzemekkkYT/RaftMIDI\n"
        )
        notesheet.write(f"|{file_name.split('/')[-1]}|RaftMIDI|1.0\n")

        notes_per_start = {}
        for note in notes:
            start = note[1]
            if start not in notes_per_start:
                notes_per_start[start] = [note]
            if start in notes_per_start and note not in notes_per_start[start]:
                notes_per_start[start].append(note)

        for i, (start, _notes) in enumerate(notes_per_start.items()):
            ret_keys = ""
            ret_modifier = ""
            ret_howLong = 0.0
            ret_tillNext = 0.0
            for _note in _notes:
                if len(_notes) > 1:
                    if _note[0] in notes_with_space:
                        notesheet.write(f"{notes_to_keys[_note[0]]} SP 0.001 0.0\n")
                        break
                    elif _note[0] in notes_with_shift:
                        notesheet.write(f"{notes_to_keys[_note[0]]} SH 0.001 0.0\n")
                        break
                elif len(_notes) == 1:
                    if _note[0] in notes_with_space:
                        # print("SP")
                        ret_modifier = "SP"
                    elif _note[0] in notes_with_shift:
                        # print("SH")
                        ret_modifier = "SH"

                if (x := f"{notes_to_keys[_note[0]]}") not in ret_keys:
                    ret_keys += f"{x}|"

                # print(f"{start=} | {min_end=} | {ret_howLong=} | {ret_tillNext=}")

            min_end = min(_notes, key=lambda x: x[2])[2]

            ret_howLong = (
                (min_end - start) / 1000 / tpms[nearest_lower(tpms.keys(), start)]
            )
            # print((i + 1 if i < len(notes_per_start) else len(notes_per_start)))
            ret_tillNext = (
                (
                    list(notes_per_start.keys())[
                        (
                            i + 1
                            if i < len(notes_per_start) - 1
                            else len(notes_per_start) - 1
                        )
                    ]
                    - min_end
                )
                / 1000
                / tpms[nearest_lower(tpms.keys(), start)]
            )

            if ret_howLong < 0:
                ret_howLong = 0.0
            if ret_tillNext < 0:
                ret_tillNext = 0.0

            if len(ret_keys) > 0:
                # print(f"{i=} | {len(notes_per_start) - 1}")
                if i != len(notes_per_start) - 1:
                    notesheet.write(
                        f"{ret_keys[:-1]} {ret_modifier} {ret_howLong:.4f} {ret_tillNext:.4f}\n"
                    )
                else:
                    notesheet.write(
                        f"{ret_keys[:-1]} {ret_modifier} {ret_howLong:.4f} {ret_tillNext:.4f}"
                    )

        # print(notes_per_start)


def notesheet_v2(file_name, tpms, notes):
    with open(f"output/{file_name}.notesheet", "w+") as notesheet:
        notesheet.write(
            "#File generated using https://github.com/PrzemekkkYT/RaftMIDI\n"
        )
        notesheet.write(f"|{file_name.split('/')[-1]}|RaftMIDI|2.0\n")

        notes_per_start = {}
        for note in notes:
            start = note[1]
            if start not in notes_per_start:
                notes_per_start[start] = [note]
            if start in notes_per_start and note not in notes_per_start[start]:
                notes_per_start[start].append(note)

        for note, start, end in notes:
            ret_modifier = ""

            if note in notes_with_space:
                ret_modifier = "SP"
            elif note in notes_with_shift:
                ret_modifier = "SH"

            if len(notes_per_start[start]) > 1:
                end = start + 0.1

            start = start / 1000 / tpms[nearest_lower(tpms.keys(), start)]
            end = end / 1000 / tpms[nearest_lower(tpms.keys(), start)]

            new_line = "\n"
            notesheet.write(
                f"{notes_to_keys[note]} {ret_modifier} {start:.4f} {end:.4f}{new_line if (note, start, end) != notes[-1] else ''}"
            )


if __name__ == "__main__":
    csv_string, track_num, file_path, file_name = start()
    export_type = input(
        "Do you want to export as .ahk or RandomThingsIveDone's Notesheet\nOptions: ahk | n1 | n2\n"
    )

    tpms, timestamps, notes = get_timestamps(csv_string, track_num)

    # print(f"{timestamps=}")
    # print(f"{notes=}")
    # print("====================================================================")
    # print(f"{tpms=}")
    # print(f"{bpm=} | {ppq=} | t/s={bpm*ppq/60}")

    pathlib.Path("./output").mkdir(parents=True, exist_ok=True)

    if export_type == "ahk":
        ahk(file_name, tpms, timestamps)
    elif export_type == "n":
        notesheet_v1(file_name, tpms, notes)
    elif export_type == "n2":
        notesheet_v2(file_name, tpms, notes)
    else:
        print("No type selected. Conversion aborted.")
