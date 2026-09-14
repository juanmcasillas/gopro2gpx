import datetime
from types import SimpleNamespace

import pytest

from gopro2gpx import fourCC
from gopro2gpx.gopro2gpx import BuildGPSPoints


def test_gps5_frequency_is_derived_from_gpsu_timestamps():
    start = datetime.datetime(2026, 1, 1)
    samples = [fourCC.GPSData(1, 2, 3, 4, 5)] * 10
    data = [
        SimpleNamespace(fourCC="SCAL", data=fourCC.GPSData(1, 1, 1, 1, 1)),
        SimpleNamespace(fourCC="GPSU", data=start),
        SimpleNamespace(fourCC="GPSF", data=3),
        SimpleNamespace(fourCC="GPS5", data=samples),
        SimpleNamespace(fourCC="GPSU", data=start + datetime.timedelta(milliseconds=990)),
        SimpleNamespace(fourCC="GPS5", data=samples),
    ]

    points, _, _ = BuildGPSPoints(data)

    assert (points[1].time - points[0].time).total_seconds() == pytest.approx(0.1)
    assert points[10].time == start + datetime.timedelta(milliseconds=990)
    assert (points[11].time - points[10].time).total_seconds() == pytest.approx(0.1)
