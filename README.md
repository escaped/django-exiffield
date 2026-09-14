# django-exiffield

![PyPI](https://img.shields.io/pypi/v/django-exiffield?style=flat-square)
![GitHub Workflow Status (master)](https://img.shields.io/github/workflow/status/escaped/django-exiffield/Test%20&%20Lint/master?style=flat-square)
![Coveralls github branch](https://img.shields.io/coveralls/github/escaped/django-exiffield/master?style=flat-square)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-exiffield?style=flat-square)
![PyPI - License](https://img.shields.io/pypi/l/django-exiffield?style=flat-square)

django-exiffield extracts exif information by utilizing the exiftool.

## Requirements

* Python 3.10 or newer
* [exiftool](https://exiftool.org/)
* Django >= 5.2 (5.2 LTS, 6.0 and 6.1 are tested)

## Installation

1. Install django-exiffield

   ```sh
   pip install django-exiffield
   ```

2. Make sure `exiftool` is executable from you environment.

## Integration

Let's assume we have an image Model with a single `ImageField`.
To extract exif information for an attached image, add an `ExifField`,
specify the name of the `ImageField` in the `source` argument

```python
from django.db import models

from exiffield.fields import ExifField


class Image(models.Model):
    image = models.ImageField()
    exif = ExifField(
        source='image',
    )
```

and create a migration for the new field.
That's it.

After attaching an image to your `ImageField`, the exif information is stored
as a `dict` on the `ExifField`.
Each exif information of the dictionary consists of two keys:

* `desc`: A human readable description
* `val`: The value for the entry.

In the following example we access the camera model

```python
image = Image.objects.get(...)
print(image.exif['Model'])
# {
#     'desc': 'Camera Model Name',
#     'val': 'DMC-GX7',
# }
```

As the exif information is encoded in a simple `dict` you can iterate and access
the values with all familiar dictionary methods.

## Denormalizing Fields

The `ExifField` stores a generic exif document, so JSON lookups such as
`exif__Model__val` work, but they are not indexable like dedicated columns.
The `ExifField` provides a convenient way to denormalize certain values using
the `denormalized_fields` argument.
It takes a dictionary with the target field as key and a simple getter function of
type `Callable[[Dict[Dict[str, str]]], Any]`.
To denormalize a simple value you can use the provided `exiffield.getters.exifgetter`

```python
from django.db import models

from exiffield.fields import ExifField
from exiffield.getters import exifgetter


class Image(models.Model):
    image = models.ImageField()
    camera = models.CharField(
        editable=False,
        max_length=100,
    )
    exif = ExifField(
        source='image',
        denormalized_fields={
            'camera': exifgetter('Model'),
        },
    )
```

There are more predefined getters in `exiffield.getters`:

`exifgetter(exif_key: str) -> str`  
Get an unmodified exif value.

`get_type() -> str`  
Get file type, e.g. video or image

`get_datetaken -> Optional[datetime]`  
Get when the file was created as `datetime`. The result is timezone-aware when
the exif data contains a parseable offset (`OffsetTimeOriginal`/`OffsetTime`)
or a `GPSDateTime` value, which is UTC by definition; otherwise it is naive.

`get_orientation  -> exiffield.getters.Orientation`  
Get orientation of media file.
Possible values are `LANDSCAPE` and `PORTRAIT`.

`get_sequencetype -> exiffield.getters.Mode`  
Guess if the image was taken in a sequence.
Possible values are `BURST`, `BRACKETING`, `TIMELAPSE` and `SINGLE`.

`get_sequencenumber -> int`  
Get image position in a sequence.

### Timezones

ExifTool stores `DateTimeOriginal` as local time without a timezone, so
`get_datetaken` can only return a naive `datetime` for files that do not carry
a usable offset or GPS time. An unparseable offset raises an `ExifError`
instead of silently producing a naive datetime. With `USE_TZ = True`, wrap the value with
`django.utils.timezone.make_aware` using the timezone the photos were taken in,
e.g. in a custom getter:

```python
from zoneinfo import ZoneInfo

from django.utils import timezone

from exiffield.getters import get_datetaken


def get_datetaken_aware(exif):
    taken = get_datetaken(exif)
    if timezone.is_naive(taken):
        taken = timezone.make_aware(taken, ZoneInfo('Europe/Berlin'))
    return taken
```

## Development

This project uses [uv](https://docs.astral.sh/uv/) for packaging and managing
all dependencies. [ruff](https://docs.astral.sh/ruff/) handles formatting and
linting and [mypy](https://mypy-lang.org/) is used for type checking.

Clone this repository and run

```bash
uv sync
```

to create a virtual environment containing all dependencies.
The test suite requires `exiftool` to be installed and executable.
Afterwards, you can run the test suite using

```bash
uv run pytest
```

and the linters using

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
```

This repository follows the [Conventional Commits](https://www.conventionalcommits.org/)
style.

## Why is the exif data not editable?

`ExifField` sets `editable=False` on purpose: the data describes the file it
was extracted from. Making it editable raises questions the library cannot
answer — should changes be written back into the file? What happens to edits
when a new file is uploaded? To keep the stored data consistent, the field is
managed by the library and overwritten whenever a new file is extracted.

If you need to display or edit exif values in a form, keep the extracted data
separate from user input:

- To display values read-only, exclude the field from the form and render
  `instance.exif` in the template.
- To let users edit values, add a regular editable field (e.g. a `JSONField`)
  and copy the extracted values into it once, so later user edits are kept:

```python
from django.db import models

from exiffield.fields import ExifField


class Image(models.Model):
    image = models.ImageField()
    exif = ExifField(source='image')
    exif_notes = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)
        if created and self.exif:
            # seed the editable copy once, then leave user edits alone
            self.exif_notes = self.exif
            super().save(update_fields=['exif_notes'])
```

The second `save()` is needed because the exif data is extracted in the
field's `pre_save` handler, i.e. during the first `save()`. After that, user
edits — including clearing the field — are preserved.

## Asynchronous extraction

Exif extraction runs synchronously in `pre_save` by default. If exiftool is
slow or your storage is remote, pass `sync=False` and run the extraction from
a background task:

```python
class Photo(models.Model):
    image = models.ImageField()
    exif = ExifField(source='image', sync=False)
```

```python
from celery import shared_task


@shared_task
def extract_exif(pk):
    photo = Photo.objects.get(pk=pk)
    Photo._meta.get_field('exif').update_exif(photo, commit=True)
```

Enqueue the task after the file has been saved (e.g. from a `post_save`
receiver) so the file is committed to storage before exiftool reads it.
`commit=True` saves the extracted data and fills `denormalized_fields`;
with `commit=False` only the in-memory instance is updated. The same pattern
works with RQ, Django-Q and other background workers.
