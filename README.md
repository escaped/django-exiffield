# django-exiffield

![PyPI](https://img.shields.io/pypi/v/django-exiffield?style=flat-square)
![GitHub Workflow Status (master)](https://img.shields.io/github/workflow/status/escaped/django-exiffield/Test%20&%20Lint/master?style=flat-square)
![Coveralls github branch](https://img.shields.io/coveralls/github/escaped/django-exiffield/master?style=flat-square)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-exiffield?style=flat-square)
![PyPI - License](https://img.shields.io/pypi/l/django-exiffield?style=flat-square)

django-exiffield extracts exif information by utilizing the exiftool.

## Requirements

* Python 3.6.1 or newer
* [exiftool](https://www.sno.phy.queensu.ca/~phil/exiftool/)
* Django >= 2.2

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

Since the `ExifField` stores its data simply as text, it is not possible to filter
or access indiviual values efficiently.
The `ExifField` provides a convinient way to denormalize certain values using
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
Get when the file was created as `datetime`

`get_orientation  -> exiffield.getters.Orientation`  
Get orientation of media file.
Possible values are `LANDSCAPE` and `PORTRAIT`.

`get_sequenctype -> exiffield.getters.Mode`  
Guess if the image was taken in a sequence.
Possible values are `BURST`, `BRACKETING`, `TIMELAPSE` and `SINGLE`.

`get_sequencenumber -> int`  
Get image position in a sequence.

## Development

This project uses [poetry](https://poetry.eustace.io/) for packaging and
managing all dependencies and [pre-commit](https://pre-commit.com/) to run
[flake8](http://flake8.pycqa.org/), [isort](https://pycqa.github.io/isort/),
[mypy](http://mypy-lang.org/) and [black](https://github.com/python/black).

Clone this repository and run

```bash
poetry install
poetry run pre-commit install
```

to create a virtual enviroment containing all dependencies.
Afterwards, You can run the test suite using

```bash
poetry run pytest
```

This repository follows the [Conventional Commits](https://www.conventionalcommits.org/)
style.

### Cookiecutter template

This project was created using [cruft](https://github.com/cruft/cruft) and the
[cookiecutter-pyproject](https://github.com/escaped/cookiecutter-pypackage) template.
In order to update this repository to the latest template version run

```sh
cruft update
```

in the root of this repository.

