import datetime
import enum
from typing import Any, Callable, Dict, Optional

from .exceptions import ExifError

ExifType = Dict[str, Dict[str, Any]]


class Orientation(enum.Enum):
    LANDSCAPE = 'landscape'
    PORTRAIT = 'landscape'


class Mode(enum.Enum):
    TIMELAPSE = 'timelapse'
    BURST = 'burst'
    BRACKETING = 'bracketing'
    SINGLE = 'single'


def exifgetter(field: str) -> Callable[[ExifType], Any]:
    """
    Return the unmodified value.
    """
    def inner(exif: ExifType) -> Any:
        return exif[field]['val']
    inner.__name__ = f'exifgetter(\'{field}\')'
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
    for key in ['DateTimeOriginal', 'GPSDateTime']:
        try:
            datetime_str = exif[key]['val']
        except KeyError:
            continue

        try:
            return datetime.datetime.strptime(
                datetime_str,
                '%Y:%m:%d %H:%M:%S',
            )
        except ValueError as e:
            raise ExifError(f'Could not parse {datetime_str}') from e
    raise ExifError(f'Could not find date')


def get_orientation(exif: ExifType) -> Orientation:
    """
    Return orientation of the file.
    """
    orientation = exif['Orientation']['val']

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
