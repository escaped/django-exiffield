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


def _parse_exif_datetime(value: str) -> datetime.datetime | None:
    """
    Parse an exif datetime string, with or without an UTC offset.
    """
    for format_ in ['%Y:%m:%d %H:%M:%S%z', '%Y:%m:%d %H:%M:%S']:
        try:
            return datetime.datetime.strptime(value, format_)
        except ValueError:
            continue
    return None


def get_datetaken(exif: ExifType) -> datetime.datetime | None:
    """
    Return when the file was created.

    The result is timezone-aware when the exif data provides a usable
    timezone: ``DateTimeOriginal`` is combined with ``OffsetTimeOriginal``
    or ``OffsetTime``, and ``GPSDateTime`` is UTC by definition. Only without
    any offset information, a naive datetime is returned.
    """
    original = exif.get('DateTimeOriginal', {}).get('val')
    offset = exif.get('OffsetTimeOriginal', {}).get('val') or exif.get(
        'OffsetTime', {}
    ).get('val')

    if original and offset:
        parsed_with_offset = _parse_exif_datetime(f'{original}{offset}')
        if parsed_with_offset:
            return parsed_with_offset

    gps = exif.get('GPSDateTime', {}).get('val')
    if gps:
        parsed_gps = _parse_exif_datetime(gps)
        if parsed_gps:
            if parsed_gps.tzinfo is None:
                # GPSDateTime is UTC even when exiftool omits the suffix
                return parsed_gps.replace(tzinfo=datetime.timezone.utc)
            return parsed_gps
        if not original:
            raise ExifError(f'Could not parse {gps}')

    if original:
        parsed_original = _parse_exif_datetime(original)
        if parsed_original:
            if offset:
                raise ExifError(f'Could not parse {offset}')
            return parsed_original
        raise ExifError(f'Could not parse {original}')

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
