from pathlib import Path

import pytest

from .models import Image

DIR = Path(__file__).parent
IMAGE_NAME = 'P1240157.JPG'


@pytest.fixture
def img(mocker):
    img = Image()
    with open(DIR / IMAGE_NAME, mode='rb') as fh:
        img.image.save(IMAGE_NAME, fh)
    img.save()
    return img


@pytest.mark.django_db
def test_exiftool(img):
    img.refresh_from_db()  # exif should be in the database

    assert len(img.exif) > 0  # at least one EXIF tag
    assert 'Aperture' in img.exif
    assert img.exif['Aperture'] == {
        'desc': 'Aperture',
        'val': 1.7,
    }
    assert img.exif['Model'] == {
        'desc': 'Camera Model Name',
        'val': 'DMC-GX7',
    }


@pytest.mark.django_db
def test_denormalization(img):
    assert img.camera == 'DMC-GX7'


@pytest.mark.django_db
def test_denormalization_invalid_exif(img, caplog):
    # reset model
    img.camera = ''
    del img.exif['Model']

    # no error should occur if the key is not available or on any other error
    img._meta.get_field('exif').denormalize_exif(img)

    # assert logging message
    assert 'Could not execute' in caplog.text
    assert 'exifgetter' in caplog.text  # name of getter function
    assert 'Image.camera' in caplog.text  # target field

    # no data should be added
    assert img.camera == ''


@pytest.mark.xfail
def test_async():
    raise NotImplemented()
