#!/usr/bin/env python
#
# 17/02/2019
# Juan M. Casillas <juanm.casillas@gmail.com>
# https://github.com/juanmcasillas/gopro2gpx.git
#
# Released under GNU GENERAL PUBLIC LICENSE v3. (Use at your own risk)
#


import argparse
import array
import os
import platform
import re
import struct
import subprocess
import sys
import time
from collections import namedtuple
import datetime

from .config import setup_environment
from .ffmpegtools import FFMpegTools
from . import fourCC
from . import gpmf
from . import gpshelper


def BuildGPSPoints(data, skip=False, skipDop=False, dopLimit=2000):
    """
    Data comes UNSCALED so we have to do: Data / Scale.
    Do a finite state machine to process the labels.
    GET
     - SCAL     Scale value
     - GPSF     GPS Fix
     - GPSU     GPS Time
     - GPS5     GPS Data
     - GPSP     GPS Precision
    """

    points = []
    start_time = None
    SCAL = fourCC.XYZData(1.0, 1.0, 1.0)
    GPSU = None
    SYST = fourCC.SYSTData(0, 0)

    stats = {
        'ok': 0,
        'badfix': 0,
        'badfixskip': 0,
        'empty' : 0,
        'baddop': 0,
        'baddopskip': 0
    }

    # GPSP is 100x DoP 
    # https://en.wikipedia.org/wiki/Dilution_of_precision_(navigation)
    # Default value is 9999 (no lock). GoPro say that under 500 is good.
    # Wikipedia indicates: 
    #   Ideal: <100
    #   Excellent: 100-200
    #   Good: 200-500
    #   Moderate: 500-1000
    #   Fair: 1000-2000
    #   Poor: >2000

    GPSP = 9999
    GPSFIX = 0 # no lock.
    TSMP = 0
    DVNM = "Unknown"
    for d in data:
        if d.fourCC == 'SCAL':
            SCAL = d.data
        elif d.fourCC == "DVNM":
            DVNM = d.data
        elif d.fourCC == 'GPSU':
            GPSU = d.data
            if start_time is None:
                start_time = GPSU
        elif d.fourCC == 'GPSF':
            if d.data != GPSFIX:
                print("GPSFIX change to %s [%s]" % (d.data,fourCC.LabelGPSF.xlate[d.data]))
            GPSFIX = d.data

        elif d.fourCC == 'TSMP':
            if TSMP == 0:
                TSMP  = d.data
            else:
                TSMP = d.data - TSMP

        elif d.fourCC == 'GPS5':
            # we have to use the REPEAT value.
            # gopro has a 18 Hz sample of writting the GPS5 value, so use it to compute delta
            #print("len", len(d.data))
            t_delta = 1/18.0
            sample_count = 0
            for item in d.data:

                if item.lon == item.lat == item.alt == 0:
                    print("Warning: Skipping empty point")
                    stats['empty'] += 1
                    continue

                if GPSFIX == 0:
                    stats['badfix'] += 1
                    if skip:
                        print("Warning: Skipping point due GPSFIX==0")
                        stats['badfixskip'] += 1
                        continue
                
                if GPSP > dopLimit:
                    stats["baddop"] += 1
                    if skipDop:
                        print("Warning: skipping point due to GPSP>limit. GPSP: %s, limit: %s" %(GPSP, dopLimit))
                        stats["baddopskip"] += 1
                        continue
                

                retdata = [ float(x) / float(y) for x,y in zip( item._asdict().values() ,list(SCAL) ) ]


                gpsdata = fourCC.GPSData._make(retdata)
                p = gpshelper.GPSPoint(gpsdata.lat, gpsdata.lon, gpsdata.alt, GPSU + datetime.timedelta(seconds= sample_count * t_delta), gpsdata.speed)
                points.append(p)
                stats['ok'] += 1
                sample_count += 1

        elif d.fourCC == 'SYST':
            data = [ float(x) / float(y) for x,y in zip( d.data._asdict().values() ,list(SCAL) ) ]
            if data[0] != 0 and data[1] != 0:
                SYST = fourCC.SYSTData._make(data)


        elif d.fourCC == 'GPRI':
            # KARMA GPRI info

            if d.data.lon == d.data.lat == d.data.alt == 0:
                print("Warning: Skipping empty point")
                stats['empty'] += 1
                continue

            if GPSFIX == 0:
                stats['badfix'] += 1
                if skip:
                    print("Warning: Skipping point due GPSFIX==0")
                    stats['badfixskip'] += 1
                    continue

            data = [ float(x) / float(y) for x,y in zip( d.data._asdict().values() ,list(SCAL) ) ]
            gpsdata = fourCC.KARMAGPSData._make(data)

            if SYST.seconds != 0 and SYST.miliseconds != 0:
                print("XX", SYST.miliseconds)
                p = gpshelper.GPSPoint(gpsdata.lat, gpsdata.lon, gpsdata.alt, datetime.fromtimestamp(SYST.miliseconds), gpsdata.speed)
                points.append(p)
                stats['ok'] += 1

        elif d.fourCC == 'GPSP':
            if GPSP != d.data:
                # TODO: restructure to make it like the processing of GPSF
                rating = "Poor"
                if d.data < 100:    rating = "Ideal"
                elif d.data < 200:  rating = "Excellent"
                elif d.data < 500:  rating = "Good"
                elif d.data < 1000: rating = "Moderate"
                elif d.data < 2000: rating = "Fair"
                print("GPSP change to %s [%s]" %(d.data, rating))
            GPSP = d.data



    print("-- stats -----------------")
    total_points =0
    for i in stats.keys():
        total_points += stats[i]
    print("Device: %s" % DVNM)
    print("- Ok:              %5d" % stats['ok'])
    print("- GPSFIX=0 (bad):  %5d (skipped: %d)" % (stats['badfix'], stats['badfixskip']))
    print("- Empty (No data): %5d" % stats['empty'])
    print("Total points:      %5d" % total_points)
    print("--------------------------")
    return(points, start_time, DVNM)

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="count")
    parser.add_argument("-b", "--binary", help="read data from bin file", action="store_true")
    parser.add_argument("-s", "--skip", help="Skip bad points (GPSFIX=0)", action="store_true", default=False)
    parser.add_argument("--skip-dop", help="Skip high Dilution of Precision points (GPSP>X)", action="store_true", default=False)
    parser.add_argument("--dop-limit", help="Dilution of Precision limit", default=2000)
    parser.add_argument("files", help="Video file or binary metadata dump", nargs='*')
    parser.add_argument("outputfile", help="output file. builds KML and GPX")
    args = parser.parse_args()

    return args

def main_core(args):
    config = setup_environment(args)
    files = args.files
    output_file = args.outputfile
    points = []
    start_time = None
    ffmpegtools = FFMpegTools(ffprobe=config.ffprobe_cmd, ffmpeg=config.ffmpeg_cmd)
    data = []
    for num, filename in enumerate(files):
        reader = gpmf.GpmfFileReader(ffmpegtools, verbose=config.verbose)

        if not args.binary:
            raw_data = reader.readRawTelemetryFromMP4(filename)
        else:
            raw_data = reader.readRawTelemetryFromBinary(filename)

        if config.verbose == 2:
            binary_filename = output_file + '.%02d.bin' % (num)
            print("Creating output file for binary data: %s" % binary_filename)
            f = open(binary_filename, "wb")
            f.write(raw_data)
            f.close()

        data += gpmf.parseStream(raw_data, config.verbose)

    points, start_time, device_name = BuildGPSPoints(data, skip=args.skip, skipDop=args.skip_dop, dopLimit=args.dop_limit)

    if len(points) == 0:
        print("Can't create file. No GPS info in %s. Exitting" % args.files)
        sys.exit(0)

    kml = gpshelper.generate_KML(points)
    with open("%s.kml" % args.outputfile , "w+") as fd:
        fd.write(kml)

    #csv = gpshelper.generate_CSV(points)
    #with open("%s.csv" % args.outputfile , "w+") as fd:
    #    fd.write(csv)

    gpx = gpshelper.generate_GPX(points, start_time, trk_name=device_name)
    with open("%s.gpx" % args.outputfile , "w+") as fd:
        fd.write(gpx)

def main():
    args = parseArgs()
    main_core(args)

if __name__ == "__main__":
    main()
