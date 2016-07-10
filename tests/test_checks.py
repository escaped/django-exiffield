import pytest
from django.db import models

from exiffield.fields import ExifField


@pytest.fixture
def mocked_which(mocker):
    """
    Fake installed exiftool.
    """
    mocked_which = mocker.patch('shutil.which')
    mocked_which.return_value = '/usr/bin/exiftool'
    return mocked_which


@pytest.mark.django_db
def test_exiftool(mocked_which):
    """
    Test checks for external tool (exiftool).
    """
    class Image(models.Model):
        image = models.ImageField()
        exif = ExifField(source='image')

        class Meta:
            app_label = 'exiffield-exiftool'

    # exiftool found
    mocked_which.return_value = '/usr/bin/exiftool'

    errors = Image.check()
    assert len(errors) == 0, errors

    # exiftool not found
    mocked_which.return_value = None

    errors = Image.check()
    assert len(errors) == 1
    assert errors[0].id == 'exiffield.E001', errors


@pytest.mark.django_db
@pytest.mark.parametrize('kwargs, error', [
    ({}, 'exiffield.E002'),  # `source` is not defined
    ({'source': 'foobar'}, 'exiffield.E003'),  # `source` not found on model
    ({'source': 'name'}, 'exiffield.E004'),  # `source` should be FileField
])
def test_source(mocked_which, kwargs, error):
    """
    Test checks for exif source.
    """
    class Image(models.Model):
        name = models.IntegerField()
        exif = ExifField(**kwargs)

        class Meta:
            # Model gets registered on every call
            # hence we need to change the `app_label` to avoid a warning...
            app_label = f'exiffield-{error}'

    errors = Image.check()
    assert len(errors) == 1
    assert errors[0].id == error, errors


@pytest.mark.django_db
@pytest.mark.parametrize('denormalized_fields, error', [
    ([], 'exiffield.E005'),  # invalid type
    ({'model_field': lambda exif: ''}, 'exiffield.E006'),  # field not found on model
    ({'camera': lambda exif: ''}, 'exiffield.E007'),  # field is editable...
    ({'datetaken': 'DateTimeOriginal'}, 'exiffield.E008'),  # value should be a callable
])
def test_fields(mocked_which, denormalized_fields, error):
    """
    Test checks for denormalized fields.
    """
    class Image(models.Model):
        image = models.ImageField()
        camera = models.CharField(max_length=100)
        datetaken = models.DateTimeField(editable=False)
        exif = ExifField(source='image', denormalized_fields=denormalized_fields)

        class Meta:
            # Model gets registered on every call
            # hence we need to change the `app_label` to avoid a warning...
            app_label = f'exiffield-{error}'

    errors = Image.check()
    assert len(errors) == 1, error
    assert errors[0].id == error, errors


@pytest.mark.django_db
def test_valid_definition(mocked_which):
    """
    Test for valid field definition.
    """
    from .models import Image

    errors = Image.check()
    assert len(errors) == 0
