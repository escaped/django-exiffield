from pathlib import Path

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.html import parse_html

from .models import Image

DIR = Path(__file__).parent
IMAGE_NAME = 'P1240157.JPG'
UPLOAD_URL = '/images/new/'
UPLOAD_INPUT = (
    '<input accept="image/*" id="id_image" name="image" required type="file">'
)


@pytest.fixture(autouse=True)
def cleanup_upload():
    yield
    (Path(settings.MEDIA_ROOT) / IMAGE_NAME).unlink(missing_ok=True)


def upload_image():
    with open(DIR / IMAGE_NAME, mode='rb') as fh:
        return SimpleUploadedFile(IMAGE_NAME, fh.read(), content_type='image/jpeg')


def assert_detail_dom(html):
    assert html.count(parse_html('<dd id="camera">DMC-GX7</dd>')) == 1
    assert html.count(parse_html('<dd id="model">DMC-GX7</dd>')) == 1
    assert html.count(parse_html('<dd id="aperture">1.7</dd>')) == 1
    assert html.count(parse_html(f'<dd id="filename">{IMAGE_NAME}</dd>')) == 1


@pytest.mark.django_db
def test_upload_form_renders_controls(client):
    response = client.get(UPLOAD_URL)
    html = parse_html(response.content.decode())

    assert response.status_code == 200
    assert html.count(parse_html('<h1>Upload image</h1>')) == 1
    assert html.count(parse_html(UPLOAD_INPUT)) == 1
    assert html.count(parse_html('<button type="submit">Upload</button>')) == 1


@pytest.mark.django_db
def test_upload_form_rejects_missing_file(client):
    response = client.post(UPLOAD_URL, {})

    assert response.status_code == 200
    assert Image.objects.count() == 0
    assert 'This field is required.' in response.content.decode()


@pytest.mark.django_db
def test_upload_extracts_exif_and_persists_it(client):
    response = client.post(UPLOAD_URL, {'image': upload_image()}, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [('/images/1/', 302)]

    image = Image.objects.get()
    assert image.camera == 'DMC-GX7'
    assert image.exif['Model'] == {'desc': 'Camera Model Name', 'val': 'DMC-GX7'}
    assert image.exif['Aperture'] == {'desc': 'Aperture', 'val': 1.7}
    assert image.exif['FileName']['val'] == IMAGE_NAME

    assert_detail_dom(parse_html(response.content.decode()))


@pytest.mark.django_db
def test_detail_page_reads_persisted_exif(client):
    client.post(UPLOAD_URL, {'image': upload_image()})

    response = client.get('/images/1/')

    assert response.status_code == 200
    assert_detail_dom(parse_html(response.content.decode()))
