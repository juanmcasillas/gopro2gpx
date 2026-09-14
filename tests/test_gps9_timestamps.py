from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from gopro2gpx import fourCC, gopro2gpx


@pytest.mark.parametrize(
    "days, milliseconds, expected",
    [
        (0, 0, datetime(2000, 1, 1, tzinfo=timezone.utc)),
        (1, 125, datetime(2000, 1, 2, 0, 0, 0, 125000, tzinfo=timezone.utc)),
        (59, 86399999, datetime(2000, 2, 29, 23, 59, 59, 999000, tzinfo=timezone.utc)),
        (60, 45296789, datetime(2000, 3, 1, 12, 34, 56, 789000, tzinfo=timezone.utc)),
    ],
)
def test_gps9_timestamp_is_utc(days, milliseconds, expected):
    data = [
        SimpleNamespace(
            fourCC="SCAL",
            data=(10000000, 10000000, 1000, 1000, 1000, 1, 1000, 100, 1),
        ),
        SimpleNamespace(fourCC="GPS9", data=[
            fourCC.GPS9Data(510000000, -10000000, 10000, 2000, 2000,
                           days, milliseconds, 100, 3),
        ]),
    ]

    points, start_time, _ = gopro2gpx.BuildGPSPoints(data)

    assert len(points) == 1
    assert points[0].time == expected
    assert points[0].time.tzinfo == timezone.utc
    assert start_time == expected


@pytest.mark.parametrize("time_shift", [-90, 90])
def test_gps9_point_timestamp_applies_explicit_shift(time_shift):
    data = [
        SimpleNamespace(fourCC="SCAL", data=(1,) * 9),
        SimpleNamespace(fourCC="GPS9", data=[
            fourCC.GPS9Data(51, -1, 10, 2, 2, 1, 30, 1, 3),
        ]),
    ]

    points, _, _ = gopro2gpx.BuildGPSPoints(data, timeShift=time_shift)

    expected = datetime(2000, 1, 2, 0, 0, 30, tzinfo=timezone.utc)
    assert points[0].time == expected - timedelta(seconds=time_shift)
