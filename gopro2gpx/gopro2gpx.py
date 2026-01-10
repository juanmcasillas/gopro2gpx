
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

# Función para obtener la ruta correcta en modo normal o frozen (PyInstaller onefile)
def resource_path(relative_path):
    """
    Obtiene la ruta absoluta al recurso, ya sea en modo normal o frozen.
    """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

# Importar módulos del paquete
from .config import setup_environment
from .ffmpegtools import FFMpegTools
from . import fourCC
from . import gpmf
from . import gpshelper
from . import VERSION

def BuildGPSPoints(data, skip=False, skipDop=False, dopLimit=2000, timeShift=0):
    """
    Procesa los datos extraídos y genera una lista de puntos GPS.

    [Sin cambios en esta función...]
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

    GPSP = None
    GPSFIX = 0
    TSMP = 0
    DVNM = "Unknown"

    for d in data:
        # print("fourCC: {}".format(d.fourCC))
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
                print("GPSFIX change to %s [%s]" % (d.data, fourCC.LabelGPSF.xlate[d.data]))
            GPSFIX = d.data
        elif d.fourCC == 'TSMP':
            if TSMP == 0:
                TSMP  = d.data
            else:
                TSMP = d.data - TSMP
        elif d.fourCC == 'GPS5':
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
                if GPSP is not None and GPSP > dopLimit:
                    stats["baddop"] += 1
                    if skipDop:
                        print("Warning: skipping point due to GPSP>limit. GPSP: %s, limit: %s" % (GPSP, dopLimit))
                        stats["baddopskip"] += 1
                        continue
                retdata = [ float(x) / float(y) for x,y in zip(item._asdict().values(), list(SCAL)) ]
                gpsdata = fourCC.GPSData._make(retdata)
                gpstime = GPSU + datetime.timedelta(seconds=sample_count*t_delta) + datetime.timedelta(seconds=timeShift)
                p = gpshelper.GPSPoint(gpsdata.lat, gpsdata.lon, gpsdata.alt, gpstime, gpsdata.speed, 'GPS5')
                points.append(p)
                stats['ok'] += 1
                sample_count += 1
        elif d.fourCC == 'GPS9':
            for item in d.data:
                GPSFIX = item.fix
                GPSP = item.dop
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
                if GPSP is not None and GPSP > dopLimit:
                    stats["baddop"] += 1
                    if skipDop:
                        print("Warning: skipping point due to GPSP>limit. GPSP: %s, limit: %s" % (GPSP, dopLimit))
                        stats["baddopskip"] += 1
                        continue
                retdata = [ float(x) / float(y) for x,y in zip(item._asdict().values(), list(SCAL)) ]
                gpsdata = fourCC.GPS9Data._make(retdata)
                target_date = datetime.datetime(2000, 1, 1) + datetime.timedelta(days=gpsdata.days_since_2000)
                time_of_day = datetime.timedelta(seconds=gpsdata.secs_since_midnight)
                gps_time = (target_date + time_of_day) - datetime.timedelta(seconds=3600) - datetime.timedelta(seconds=timeShift)
                if start_time is None:
                    start_time = gps_time
                p = gpshelper.GPSPoint(gpsdata.lat, gpsdata.lon, gpsdata.alt, gps_time, gpsdata.speed, 'GPS9')
                points.append(p)
                stats['ok'] += 1
        elif d.fourCC == 'SYST':
            data_vals = [ float(x) / float(y) for x,y in zip(d.data._asdict().values(), list(SCAL)) ]
            if data_vals[0] != 0 and data_vals[1] != 0:
                SYST = fourCC.SYSTData._make(data_vals)
        elif d.fourCC == 'GPRI':
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
            data_vals = [ float(x) / float(y) for x,y in zip(d.data._asdict().values(), list(SCAL)) ]
            gpsdata = fourCC.KARMAGPSData._make(data_vals)
            if SYST.seconds != 0 and SYST.miliseconds != 0:
                syst_time = datetime.datetime.fromtimestamp(SYST.miliseconds) - datetime.timedelta(seconds=timeShift)
                p = gpshelper.GPSPoint(gpsdata.lat, gpsdata.lon, gpsdata.alt, syst_time, gpsdata.speed)
                points.append(p)
                stats['ok'] += 1
        elif d.fourCC == 'GPSP':
            if GPSP != d.data:
                print("GPSP change to %s [%s]" % (d.data, fourCC.LabelGPSP.xlate(d.data)))
            GPSP = d.data

    print("-- stats -----------------")
    total_points = sum(stats.values())
    print("Device: %s" % DVNM)
    print("- Ok:              %5d" % stats['ok'])
    print("- GPSFIX=0 (bad):  %5d (skipped: %d)" % (stats['badfix'], stats['badfixskip']))
    print("- GPSP>%4d (bad): %5d (skipped: %d)" % (dopLimit, stats['baddop'], stats['baddopskip']))
    print("- Empty (No data): %5d" % stats['empty'])
    print("Total points:      %5d" % total_points)
    print("--------------------------")
    if timeShift > 0:
        print(f"Timestamp shifted: {timeShift}s")
        start_time = start_time - datetime.timedelta(seconds=timeShift)
    return (points, start_time, DVNM)


def parseArgs():
    version_text = f"gopro2gpx version {VERSION}"
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="count")
    parser.add_argument("-b", "--binary", help="read data from bin file", action="store_true")
    parser.add_argument("-s", "--skip", help="Skip bad points (GPSFIX=0)", action="store_true", default=False)
    parser.add_argument("--skip-dop", help="Skip high Dilution of Precision points (GPSP>X)", action="store_true", default=False)
    parser.add_argument("--dop-limit", help="Dilution of Precision limit", default=2000, type=int)
    parser.add_argument("--time-shift", help="Shift Timestamps by X seconds", default=0, type=int)
    parser.add_argument("--gpx", help="Generate only GPX output", action="store_true", default=False)
    parser.add_argument("--kml", help="Generate only KML output", action="store_true", default=False)
    parser.add_argument("--csv", help="Generate only CSV output", action="store_true", default=False)
    # Opción para modo GUI
    parser.add_argument("--gui", help="Run in GUI mode (do not exit after file generation)", action="store_true", default=False)
    parser.add_argument("--version", help="show the gopro2gpx version and exit", action="version", version=version_text)
    parser.add_argument("files", help="Video file or binary metadata dump", nargs='+')
    parser.add_argument("outputfile", help="output file prefix. Builds KML, GPX y CSV by default")
    return parser.parse_args()

def main_core(args):
    # Aseguramos que args.gui exista
    if not hasattr(args, 'gui'):
        args.gui = False

    config = setup_environment(args)
    
    files = args.files
    output_file = args.outputfile
    ffmpegtools = FFMpegTools(ffprobe=config.ffprobe_cmd, ffmpeg=config.ffmpeg_cmd)
    data = []
    for num, filename in enumerate(files):
        reader = gpmf.GpmfFileReader(ffmpegtools, verbose=config.verbose)
        if not args.binary:
            raw_data = reader.readRawTelemetryFromMP4(filename)
        else:
            raw_data = reader.readRawTelemetryFromBinary(filename)
        if config.verbose == 2:
            binary_filename = f"{output_file}.{num:02d}.bin"
            print("Creating output file for binary data: %s" % binary_filename)
            with open(binary_filename, "wb") as f:
                f.write(raw_data)
        data += gpmf.parseStream(raw_data, config.verbose)

    points, start_time, device_name = BuildGPSPoints(data, skip=args.skip, skipDop=args.skip_dop, dopLimit=args.dop_limit, timeShift=args.time_shift)
    if len(points) == 0:
        print("Can't create file. No GPS info in %s. Exiting" % args.files)
        if not args.gui:
            sys.exit(0)
        else:
            return

    # Determinar cuántos formatos se solicitaron; si ninguno, se generan los tres.
    num_formats = 0
    if args.gpx: num_formats += 1
    if args.kml: num_formats += 1
    if args.csv: num_formats += 1
    if num_formats == 0:
        num_formats = 3

    # Generar KML si se solicitó o si se generan todos
    if args.kml or num_formats == 3:
        kml = gpshelper.generate_KML(points)
        with open(f"{output_file}.kml", "w") as fd:
            fd.write(kml)
        print("Archivo KML generado: {}.kml".format(output_file))
        if (args.kml and not args.gpx and not args.csv) and (not args.gui):
            sys.exit()

    # Generar GPX si se solicitó o si se generan todos
    if args.gpx or num_formats == 3:
        gpx = gpshelper.generate_GPX(points, start_time, trk_name=device_name)
        with open(f"{output_file}.gpx", "w") as fd:
            fd.write(gpx)
        print("Archivo GPX generado: {}.gpx".format(output_file))
        if (args.gpx and not args.kml and not args.csv) and (not args.gui):
            sys.exit()

    # Generar CSV si se solicitó o si se generan todos
    if args.csv or num_formats == 3:
        csv_data = gpshelper.generate_CSV(points, start_time, trk_name=device_name)
        with open(f"{output_file}.csv", "w", newline='') as fd:
            fd.write(csv_data)
        print("Archivo CSV generado: {}.csv".format(output_file))
    # En modo GUI, simplemente retornamos sin llamar a sys.exit().

def main():
    args = parseArgs()
    args.gui = getattr(args, 'gui', False)
    main_core(args)

if __name__ == "__main__":
    main()
