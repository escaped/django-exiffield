import datetime
from collections.abc import Callable
from typing import Any, cast

from django.db import models

from .exceptions import ExifError

ExifType = dict[str, dict[str, Any]]


class Orientation(models.TextChoices):
    LANDSCAPE = 'landscape'
    PORTRAIT = 'portrait'


class Mode(models.TextChoices):
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

    inner.__name__ = f'exifgetter("{field}")'
    return inner


def get_type(exif: ExifType) -> str:
    """
    Return type of file, e.g. image.
    """
    return exif['MIMEType']['val'].split('/')[0]


def get_datetaken(exif: ExifType) -> datetime.datetime | None:
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
    raise ExifError('Could not find date')


def get_orientation(exif: ExifType) -> Orientation:
    """
    Return orientation of the file.
    """
    orientation = exif.get('Orientation', {}).get('num', 1)

    width, height = exif['ImageWidth']['val'], exif['ImageHeight']['val']
    if orientation > 4:
        # image rotated image by 90 degrees
        width, height = height, width
    if width < height:
        return cast(Orientation, Orientation.PORTRAIT)
    return cast(Orientation, Orientation.LANDSCAPE)


def get_sequencetype(exif: ExifType) -> Mode:
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
            return cast(Mode, Mode.BURST)
        if mode == 2:
            return cast(Mode, Mode.BRACKETING)

    # time lapse
    try:
        mode = exif['TimerRecording']['num']
    except KeyError:
        pass
    else:
        if mode == 1:
            return cast(Mode, Mode.TIMELAPSE)
    return cast(Mode, Mode.SINGLE)


def get_sequencenumber(exif: ExifType) -> int:
    """
    Return position of image within the recoding sequence.
    """
    try:
        return exif['SequenceNumber']['num']
    except KeyError:
        return 0
