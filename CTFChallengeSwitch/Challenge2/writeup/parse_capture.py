import argparse
import struct

from joycontrol.report import InputReport, OutputReport, SubCommand
import math
DIR = {
    0b00001000: ('LEFT', 1),
    0b00000100: ('RIGHT',2),
    0b00000010: ('UP',   3),
    0b00000001: ('DOWN', 4)
}
RUMBLE = [4, 180, 1, 78, 4, 180, 1, 78]

""" joycontrol capture parsing example.

Usage:
    parse_capture.py <capture_file>
    parse_capture.py -h | --help
"""


def _eof_read(file, size):
    """
    Raises EOFError if end of file is reached.
    """
    data = file.read(size)
    if not data:
        raise EOFError()
    return data

def get_rumble_timestamps():
    rumble_timestamps = [i[0] for i in output_reports if i[1].get_rumble_data() == RUMBLE]
    return rumble_timestamps

def get_dir_inputs():
    dir_inputs = [(i[0], i[1].data[6]) for i in input_reports if i[1].data[6] & 0b00001111 != 0]
    return dir_inputs

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('capture_file')
    args = parser.parse_args()

    # list of time, report tuples
    input_reports = []
    output_reports = []

    with open(args.capture_file, 'rb') as capture:
        try:
            start_time = None
            while True:
                # parse capture time
                time = struct.unpack('d', _eof_read(capture, 8))[0]
                
                if start_time is None:
                    start_time = time

                # parse data size
                size = struct.unpack('i', _eof_read(capture, 4))[0]
                # parse data
                data = list(_eof_read(capture, size))

                if data[0] == 0xA1:
                    report = InputReport(data)
                    # normalise time
                    input_reports.append((time, report))
                elif data[0] == 0xA2:
                    report = OutputReport(data)
                    # normalise time
                    output_reports.append((time, report))
                else:
                    raise ValueError(f'Unexpected data.')
        except EOFError:
            pass

    dir_input_list = get_dir_inputs()
    rumble_timestamps = get_rumble_timestamps()
    print(dir_input_list)
    print(rumble_timestamps)

    tailcnt = cursor = 0
    seeds = []
    # The last direction of before snake scoring a point can be found by the timestamp when the rumble packet was sent.
    for timestamp in rumble_timestamps:
        while cursor < len(dir_input_list) and dir_input_list[cursor][0] <= timestamp:
            cursor += 1
        lastdir_before_rumble = dir_input_list[cursor-1][1]

        # In order to get the formula to calculate seed, you should do reserve engineering on game nro file.
        seed = tailcnt*4 + DIR[lastdir_before_rumble][1] - 1
        seeds.append(str(seed))

        tailcnt += 1

    print(len(seeds), seeds)
    open('seeds.txt', 'w').write(' '.join(seeds))

    # now plz place seeds.txt to switch emulator's /sdcard folder
    # and then run the rand.nro file you complied just now to generate random numbers
    # You should press a key on your keyboard correspond to 'A' in Pro Controller.
    # At the end, flag will put into flag.txt


    # For Ryujinx, /sdcard can be accessed by clicking Open Ryujinx Folder under the File menu in the GUI.
    #              And key 'Z' on keyboard corresponds to 'A' in Pro Controller.




