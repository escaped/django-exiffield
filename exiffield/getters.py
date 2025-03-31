import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional

from choicesenum import ChoicesEnum

from .exceptions import ExifError

ExifType = Dict[str, Dict[str, Any]]


class Orientation(ChoicesEnum, Enum):  # NOTE inherits from `Enum` to make `mypy` happy
    LANDSCAPE = 'landscape'
    PORTRAIT = 'portrait'


class Mode(ChoicesEnum, Enum):  # NOTE inherits from `Enum` to make `mypy` happy
    TIMELAPSE = 'timelapse'
    BURST = 'burst'
    BRACKETING = 'bracketing'
    SINGLE = 'single'


def exifgetter(field: str, val='val') -> Callable[[ExifType], Any]:
    """
    Return the unmodified value.
    """

    def inner(exif: ExifType) -> Any:
        return exif[field][val]

    inner.__name__ = f'exifgetter("{field}")'
    return inner


def get_type(exif: ExifType) -> str:
    """
    Return type of file, e.g. image.
    """
    return exif['MIMEType']['val'].split('/')[0]


def get_datetaken(exif: ExifType) -> Optional[datetime.datetime]:
    """
    Return when the file was created.
    """

    def to_datetime(dt_str):
        try:
            return datetime.datetime.strptime(
                dt_str,
                '%Y:%m:%d %H:%M:%S%z',
            )
        except ValueError as e:
            raise ExifError(f'Could not parse {dt_str}') from e

    try:
        datetime_str = exif['GPSDateTime']['val']
        if datetime_str[-1] == 'Z':
            datetime_str = datetime_str[:-1] + '+00:00'
        return to_datetime(datetime_str)
    except KeyError:
        pass

    try:
        datetime_str = exif['DateTimeOriginal']['val'] + exif['OffsetTime']['val']
        return to_datetime(datetime_str)
    except KeyError:
        pass

    raise ExifError('Could not find date')


def get_orientation(exif: ExifType) -> Orientation:
    """
    Return orientation of the file.
    """
    orientation = exif['Orientation']['num']

    width, height = exif['ImageWidth']['val'], exif['ImageHeight']['val']
    if orientation > 4:
        # image rotated image by 90 degrees
        width, height = height, width
    if width < height:
        return Orientation.PORTRAIT
    return Orientation.LANDSCAPE


def get_sequencetype(exif) -> Mode:
    """
    Return the recoding mode.
    """
    # burst or bracketing
    try:
        mode = exif['BurstMode']['num']
    except KeyError:
        pass
    else:
        if mode == 1:
            return Mode.BURST
        if mode == 2:
            return Mode.BRACKETING

    # time lapse
    try:
        mode = exif['TimerRecording']['num']
    except KeyError:
        pass
    else:
        if mode == 1:
            return Mode.TIMELAPSE
    return Mode.SINGLE


def get_sequencenumber(exif) -> int:
    """
    Return position of image within the recoding sequence.
    """
    try:
        return exif['SequenceNumber']['num']
    except KeyError:
        return 0


def get_latitude(exif) -> float:
    """
    Return numeric latitude.
    """
    try:
        return exif['GPSLatitude']['num']
    except KeyError:
        return 0


def get_longitude(exif) -> float:
    """
    Return numeric longitude.
    """
    try:
        return exif['GPSLongitude']['num']
    except KeyError:
        return 0
