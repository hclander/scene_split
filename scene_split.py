#!/usr/bin/python3

import sys
import os
import subprocess

import argparse
import csv
import glob
import re
from datetime import timedelta
import math

## pyscene cvs file format
# line 00: mkvmerge split timecodes
# line 01: header field names
# line xx: Data ->  scene #, Start Frame Number, Start Timecode (HH:MM:SS.ZZZ), Start Time (seconds), Length (seconds)


def test_csv(file_name):

    # with open(file_name, 'r') as f:
    #     lines = f.read().splitlines()
    #     scenes = []
    #     for l in lines[2:]:
    #         scenes.append(l.split(','))
    #
    #     print(scenes)
    #     print()
    #
    # with open(file_name, 'r') as f:
    #     lines = f.read().splitlines()
    #     scenes = []
    #     for l in lines[2:]:
    #         row = l.split(',')
    #         scenes.append([int(row[0]), int(row[1]), row[2], float(row[3]), float(row[4])])
    #
    #     print(scenes)
    #     print()

    with open(file_name, 'r', newline='') as f:
        f.readline()
        f.readline()  # skip line 00 and 01
        reader = csv.reader(f)
        scenes = []
        for row in reader:
            scenes.append([int(row[0]), int(row[1]), row[2], float(row[3]), float(row[4])])
            # scenes.append(row)
            # print(row)

        print(scenes)
        print()


    # with open(file_name, 'r') as f:
    #     f.readline();  # skip line 00
    #     f.readline();  # skip line 01
    #
    #     scenes = []
    #     for l in f:
    #         scenes.append(l.split(','))
    #
    #     print(scenes)
    #     print()
    #
    # with open(file_name, 'r') as f:
    #     lines = f.readlines()
    #     scenes = []
    #     for l in lines[2:]:
    #         scenes.append(l.split(','))
    #
    #     print(scenes)
    #     print()
    #
    # with open(file_name, 'r') as f:
    #     lines = f.read().split('\n')
    #     scenes = []
    #     for l in lines[2:]:
    #         scenes.append(l.split(','))
    #
    #     print(scenes)
    #     print()

def parse_scene_csv_2(file_name):
    scenes = []
    with open(file_name, 'r') as f:
        lines = f.read().splitlines()
        for l in lines[2:]:
            row = l.split(',')
            scenes.append([int(row[0]), int(row[1]), row[2], float(row[3]), float(row[4])])

        return scenes


def parse_scene_csv(file_name):

    scenes = []
    with open(file_name, 'r', newline='') as f:
        f.readline()
        f.readline()  # skip line 00 and 01
        reader = csv.reader(f)
        for row in reader:
            scenes.append([int(row[0]), int(row[1]), row[2], float(row[3]), float(row[4])])

    return scenes


def parse_scene_csv_sublist(file_name, sublist=None):

    scenes = []
    with open(file_name, 'r', newline='') as f:
        f.readline()
        f.readline()  # skip line 00 and 01
        reader = csv.reader(f)
        for row in reader:
            sec_num = int(row[0])
            if not sublist or sec_num + 1 in sublist:
                scenes.append([sec_num, int(row[1]), row[2], float(row[3]), float(row[4])])

    return scenes


def split_scenes(f_csv, f_in, f_out, type, method=None, group=False, pad=0.0):

    if not f_out:
        f_out = os.path.splitext(f_csv)[0]

    print("")
    print("Output file: " + f_out + type)
    scenes = parse_scene_csv(f_csv)

    print("Total scenes: {:d}".format(len(scenes)))

    if group:
        g = []

        for i in range(len(scenes)):
            if i > 0:
                if scenes[i-1][0] == scenes[i][0]-1:
                    g[len(g)-1][4] += scenes[i][4]
                    continue

            g.append(scenes[i])

        print("Total scenes (grouped): {:d}\n".format(len(g)))
        scenes = g


    for s in scenes:
        cmd = 'ffmpeg -y -ss {time_start} -i {input} -c {method} -t {length} -avoid_negative_ts 0 {out_base}-{scene:05d}{out_type}'.format(
            input=f_in, time_start=s[2], length=s[4]+pad, method='copy', out_base=f_out, out_type=type, scene=s[0]
        )
        # print(cmd)
        print("Processing scene {:04d} ... ".format(s[0]), end='')
        err_code = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print("OK." if not err_code else "KO!")

    print()


def split_scenes_2(f_csv, f_in, f_out, type, method=None, group=False, pad=0.0):
    """ Alternative method"""

    if not f_out:
        f_out = os.path.splitext(f_csv)[0]

    print("")
    print("Output file: " + f_out + type)
    scenes = parse_scene_csv(f_csv)

    print("Total scenes: {:d}".format(len(scenes)))

    o = scenes[0]
    g = o
    n = 0
    for i in range(1, len(scenes)+1):

        s = scenes[i] if i < len(scenes) else None

        if not s or o[0] != s[0]-1 or not group:

            cmd = 'ffmpeg -y -ss {time_start} -i {input} -c {method} -t {length} -avoid_negative_ts 0 {out_base}-{scene:05d}{out_type}'.format(
                input=f_in, time_start=g[2], length=g[4] + pad, method='copy', out_base=f_out, out_type=type, scene=g[0]
            )
            # print(cmd)
            print("Processing scene {:04d} {:s} ... ".format(g[0], "(Group of {:d})".format(n+1) if n else ""), end='')
            err_code = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print("OK." if not err_code else "KO!")

            g = s
            n = 0
        elif i < len(scenes):
            g[4] += s[4]
            n += 1

        o = s

    print()


def split_scenes_3(f_csv, f_in, f_out, type, method, group=False, pad=0.0, f_dir=None):
    """ Alternative method with sublist"""

    if not f_out:
        f_out = os.path.splitext(f_csv)[0]

    print("")
    print("Output file: " + f_out + type)
    #scenes = parse_scene_csv(f_csv)
    scenes = parse_scene_csv_sublist(f_csv, subscene_list(f_in,f_dir))

    print("Total scenes: {:d}".format(len(scenes)))

    with open(f_out + '.log', 'w') as f_log:

        i = iter(scenes)
        s = next(i, None)
        o = s
        g = s
        n = 0

        while s:
            s = next(i, None)

            if not s or o[0] != s[0]-1 or not group:

                cmd = 'ffmpeg -y -ss {time_start} -i "{input}"  {method} -t {length} -avoid_negative_ts 1 {out_base}-{scene:05d}{out_type}'.format(
                    input=f_in, time_start=g[2], length=g[4] + pad, method=method, out_base=f_out, out_type=type, scene=g[0]
                )
                # print(cmd)
                print("Processing scene {:04d} {:s} ... ".format(g[0], "(Group of {:d})".format(n+1) if n else ""), end='')
                # err_code = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                err_code = subprocess.call(cmd, shell=True, stdout=f_log, stderr=f_log)

                print("OK." if not err_code else "KO!")

                g = s
                n = 0
            elif s:
                g[4] += s[4]
                n += 1

            o = s

        print()


def split_scenes_4(f_csv, f_in, f_out, type, method, group=False, pad=0.0, f_dir=None, accuracy=None):
    """ Alternative method with sublist"""

    if not f_out:
        f_out = os.path.splitext(f_csv)[0]

    print("")
    print("Output file: " + f_out + type)
    #scenes = parse_scene_csv(f_csv)
    scenes = parse_scene_csv_sublist(f_csv, subscene_list(f_in,f_dir))

    print("Total scenes: {:d}".format(len(scenes)))

    with open(f_out + '.log', 'w') as f_log:

        i = iter(scenes)
        s = next(i, None)
        o = s
        g = s
        n = 0

        while s:
            s = next(i, None)

            if not s or o[0] != s[0]-1 or not group:
                if accuracy is None or g[3]<accuracy:
                    tsf = timedelta(seconds=g[3])
                    tsa = timedelta(seconds=0)
                elif accuracy < 0:
                    tsf = timedelta(seconds=0)
                    tsa = timedelta(seconds=g[3])
                else:
                    ts = math.modf(g[3])
                    tsf = timedelta(seconds=ts[1]-accuracy)
                    tsa = timedelta(seconds=accuracy+ts[0])

                cmd = 'ffmpeg -y -ss {time_start_fast} -i "{input}" -ss {time_start_acc} {method} -t {length} -avoid_negative_ts 1 {out_base}-{scene:05d}{out_type}'.format(
                    input=f_in, time_start_fast=tsf, time_start_acc=tsa, length=g[4] + pad, method=method, out_base=f_out, out_type=type, scene=g[0]
                )
                # print(cmd)
                print("Processing scene {:04d} {:s} ... ".format(g[0], "(Group of {:d})".format(n+1) if n else ""), end='')
                # err_code = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                err_code = subprocess.call(cmd, shell=True, stdout=f_log, stderr=f_log)

                print("OK." if not err_code else "KO!")

                g = s
                n = 0
            elif s:
                g[4] += s[4]
                n += 1

            o = s

        print()


def subscene_list(f_in, f_dir):

    if not f_dir:
        return None

    f_tpl = f_dir + os.path.sep + "{:s}.Scene-*-*.jpg".format(os.path.split(f_in)[1])

    matcher = re.compile('.*-(\d+)-.*.jpg')

    l = set()

    for f in glob.iglob(f_tpl):

        m = matcher.match(f)
        if m:
            l.add(int(m.group(1)))

    return l
    # return sorted(l)


def test_timedeltas(f_in, f_csv, f_dir):
    scenes = parse_scene_csv_sublist(f_csv, subscene_list(f_in, f_dir))

    for s in scenes:
        ts = s[2]
        td = dt.timedelta(seconds=s[3])
        ld = dt.timedelta(seconds=s[4])

        print('#: {:04d} {:s} ({:f} {:s}) --> {:s} ({:f})'.format(s[0], ts, s[3], str(td), str(ld), s[4]))


def main():

    parser = argparse.ArgumentParser(description="Scene Split")
    parser.add_argument("-i", "--input", dest="input", help="Input file", required=True)
    parser.add_argument("-c", "--csv", dest="csv", help="Scene file (.csv)", required=True)
    parser.add_argument("-o", "--output", dest="output", help="Base output file", default=None)
    parser.add_argument("-t", "--type", dest="type", help="Output file type", default=".mp4")
    parser.add_argument("-g", "--group", dest="group", help="Group consecutive secuences", action="store_true", default=False)
    parser.add_argument("-p", "--pad", type=float, dest="pad", help="Add extra time (in s.) to the secuence length", default=0.0)
    parser.add_argument("-l", "--list", dest="list", help="Scene sublist from thumbnails (-si)", default=None)
    parser.add_argument("-m", "--method", dest="method", help="Encode Method params", default="-c copy")
    parser.add_argument("-a", "--accuracy", dest="accuracy", type=float, help="Seek accuracy", default=None)
    parser.add_argument("--test", dest="test", action="store_true", default=False)

    args = parser.parse_args()

    if args.test:
        test_timedeltas(args.input,args.csv, args.list)
        sys.exit()
    # if args.list:
    #
    #     sl = parse_scene_csv_sublist(args.csv, subscene_list(args.input, args.list))
    #     print(sl)
    #
    #     sys.exit(0)

    split_scenes_4(args.csv, args.input, args.output, args.type, args.method, args.group, args.pad, args.list, args.accuracy)
    # split_scenes_3(args.csv, args.input, args.output, args.type, args.method, args.group, args.pad, args.list)
    # split_scenes_2(args.csv, args.input, args.output, args.type, None, args.group, args.pad)
    # split_scenes(args.csv, args.input, args.output, args.type, None, args.group, args.pad)



if __name__ == '__main__':
    main()