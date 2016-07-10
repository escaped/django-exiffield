import datetime

import pytest

from exiffield import getters
from exiffield.exceptions import ExifError


@pytest.mark.parametrize('key, expected', [
    ['Model', 'DMC-GX7'],
    ['Aperture', 1.7],
])
def test_exifgetter(key, expected):
    exif_data = {
        'Model': {
            'desc': 'Camera Model Name',
            'val': 'DMC-GX7',
        },
        'Aperture': {
            'desc': 'Aperture',
            'val': 1.7,
        },
        'FileSize': {
            'desc': 'File Size',
            'num': 4915200,
            'val': "4.7 MB",
        }
    }

    assert getters.exifgetter(key)(exif_data) == expected


@pytest.mark.parametrize('value, expected', [
    ['image/jpeg', 'image'],
    ['video/mp4', 'video'],
])
def test_get_type(value, expected):
    exif_data = {
        'MIMEType': {'val': value},
    }

    assert getters.get_type(exif_data) == expected


@pytest.mark.parametrize('exif_data, expected', [
    [{'DateTimeOriginal': {'val': '2018:03:02 11:33:10'}},
     datetime.datetime(2018, 3, 2, 11, 33, 10)],
    [{'GPSDateTime': {'val': '2018:03:02 11:33:10'}},
     datetime.datetime(2018, 3, 2, 11, 33, 10)],
])
def test_get_datetaken(exif_data, expected):
    assert getters.get_datetaken(exif_data) == expected


@pytest.mark.parametrize('exif_data, error_msg', [
    [{'DateTimeOriginal': {'val': 'invalid format'}},
     'Could not parse'],
    [{},  # missing key
     'Could not find'],
])
def test_get_datetaken_invalid_data(exif_data, error_msg):
    with pytest.raises(ExifError) as exc_info:
        getters.get_datetaken(exif_data)
        assert error_msg in exc_info.value.message


@pytest.mark.parametrize('width, height, orientation, expected', [
    [300, 200, 1, getters.Orientation.LANDSCAPE],
    [300, 200, 2, getters.Orientation.LANDSCAPE],
    [300, 200, 3, getters.Orientation.LANDSCAPE],
    [300, 200, 4, getters.Orientation.LANDSCAPE],

    [200, 300, 1, getters.Orientation.PORTRAIT],
    [200, 300, 2, getters.Orientation.PORTRAIT],
    [200, 300, 3, getters.Orientation.PORTRAIT],
    [200, 300, 4, getters.Orientation.PORTRAIT],

    [300, 200, 5, getters.Orientation.PORTRAIT],
    [300, 200, 6, getters.Orientation.PORTRAIT],
    [300, 200, 7, getters.Orientation.PORTRAIT],
    [300, 200, 8, getters.Orientation.PORTRAIT],

    [200, 300, 5, getters.Orientation.LANDSCAPE],
    [200, 300, 6, getters.Orientation.LANDSCAPE],
    [200, 300, 7, getters.Orientation.LANDSCAPE],
    [200, 300, 8, getters.Orientation.LANDSCAPE],
])
def test_get_orientation(width, height, orientation, expected):
    exif_data = {
        'Orientation': {'val': orientation},
        'ImageWidth': {'val': width},
        'ImageHeight': {'val': height},
    }

    assert getters.get_orientation(exif_data) == expected


@pytest.mark.parametrize('exif_data, expected', [
    [{}, getters.Mode.SINGLE],
    [{'BurstMode': {'num': 2}}, getters.Mode.BRACKETING],
    [{'BurstMode': {'num': 1}}, getters.Mode.BURST],
    [{'TimerRecording': {'num': 1}}, getters.Mode.TIMELAPSE],
])
def test_get_sequencetype(exif_data, expected):
    assert getters.get_sequencetype(exif_data) == expected


@pytest.mark.parametrize('exif_data, expected', [
    [{}, 0],
    [{'SequenceNumber': {'num': 0}}, 0],
    [{'SequenceNumber': {'num': 3}}, 3],
])
def test_get_sequencenumber(exif_data, expected):
    assert getters.get_sequencenumber(exif_data) == expected
