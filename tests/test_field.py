from pathlib import Path

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from exiffield import fields

from .models import Image

DIR = Path(__file__).parent
IMAGE_NAME = 'P1240157.JPG'


@pytest.fixture
def img(mocker):
    """
    Fake an uploaded file.
    """
    img = Image()
    image_path = DIR / IMAGE_NAME
    media_image_path = Path(settings.MEDIA_ROOT) / IMAGE_NAME
    with open(image_path, mode='rb') as fh:
        image_file = SimpleUploadedFile(
            media_image_path,
            fh.read(),
        )
    img.image.file = image_file
    img.image.name = str(media_image_path)
    img.image._committed = False
    return img


@pytest.mark.django_db
def test_unsupported_file():
    img = Image()
    media_path = Path(settings.MEDIA_ROOT) / 'foo.txt'
    file_ = SimpleUploadedFile(
        media_path,
        'unsupported content'.encode('utf8'),
    )
    img.image.file = file_
    img.image.name = str(media_path)
    img.image._committed = False

    # do not fail when saving
    img.save()
    assert img.exif == {}

    # do not fail when saving and file is already saved to storage
    img.save()
    assert img.exif == {}


@pytest.mark.django_db
def test_extract_exif(mocker, img):
    img.save()
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
def test_do_not_reextract_exif(mocker, img):
    img.save()  # store image and extract exif

    exif_field = img._meta.get_field('exif')
    mocker.spy(fields, 'get_exif')

    img.save()
    assert fields.get_exif.call_count == 0

    exif_field.update_exif(img)
    assert fields.get_exif.call_count == 0


@pytest.mark.django_db
def test_do_not_extract_exif_without_file(mocker):
    mocker.spy(fields, 'get_exif')

    img = Image()
    img.save()

    assert fields.get_exif.call_count == 0
    # the fallback value should always be an empty dict
    assert img.exif == {}


@pytest.mark.django_db
def test_extract_exif_if_missing(mocker, img):
    img.save()  # store image and extract exif
    img.exif = {}

    exif_field = img._meta.get_field('exif')
    mocker.spy(fields, 'get_exif')

    exif_field.update_exif(img)
    assert fields.get_exif.call_count == 1
    assert isinstance(img.exif, dict)
    assert len(img.exif.keys()) > 0


@pytest.mark.django_db
def test_extract_exif_if_forced(mocker, img):
    img.save()  # store image and extract exif
    img.exif = {'foo': {'desc': 'Foo', 'val': 0}}

    exif_field = img._meta.get_field('exif')
    mocker.spy(fields, 'get_exif')

    exif_field.update_exif(img, force=True)
    assert fields.get_exif.call_count == 1
    assert isinstance(img.exif, dict)
    assert 'foo' not in img.exif


@pytest.mark.django_db
def test_extract_exif_if_file_changes(mocker, img):
    img.save()  # store image and extract exif
    img.exif = {'FileName': {'desc': 'File Nmae', 'val': 'foo.jpg'}}

    exif_field = img._meta.get_field('exif')
    exif_field.update_exif(img)

    assert isinstance(img.exif, dict)
    # there should be more than one key (`FileName`)
    assert len(img.exif.keys()) > 1
    filename = img.image.name.split('/')[-1]
    assert img.exif['FileName']['val'] == filename


@pytest.mark.django_db
def test_extract_exif_and_save(mocker, img):
    img.save()  # store image and extract exif
    img.exif = None

    exif_field = img._meta.get_field('exif')

    exif_field.update_exif(img, commit=True, force=True)
    img.refresh_from_db()
    assert isinstance(img.exif, dict)


@pytest.mark.django_db
def test_denormalization(img):
    img.save()  # store image and extract exif
    assert img.camera == 'DMC-GX7'


@pytest.mark.django_db
def test_denormalization_invalid_exif(img, caplog):
    img.save()  # store image and extract exif

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
