=====================
django-exiffield
=====================


.. image:: https://img.shields.io/pypi/v/django-exiffield.svg
    :target: https://pypi.python.org/pypi/django-exiffield

.. image:: https://travis-ci.org/escaped/django-exiffield.png?branch=master
    :target: http://travis-ci.org/escaped/django-exiffield
    :alt: Build Status

.. image:: https://coveralls.io/repos/escaped/django-exiffield/badge.png?branch=master
    :target: https://coveralls.io/r/escaped/django-exiffield
    :alt: Coverage

.. image:: https://img.shields.io/pypi/pyversions/django-exiffield.svg

.. image:: https://img.shields.io/pypi/status/django-exiffield.svg

.. image:: https://img.shields.io/pypi/l/django-exiffield.svg


django-exiffield extracts exif information by utilizing ``exiftool``.


Requirements
============

- `exiftool <https://www.sno.phy.queensu.ca/~phil/exiftool/>`_
- Python 3.6
- Django >= 1.8


Installation
============

#. Install django-exiffield ::

    pip install django-exiffield

#. Make sure ``exiftool`` is executable from you environment.


Integration
===========

Let's assume we have an image Model with a single ``ImageField``.
To extract exif information for an attached image, add an ``ExifField``,
specify the name of the ``ImageField`` in the ``source`` argument ::


   from django.db import models

   from exiffield.fields import ExifField


   class Image(models.Model):
       image = models.ImageField()
       exif = ExifField(
           source='image',
       )


and create a migration for the new field.
That's it.

After attaching an image to your ``ImageField``, the exif information is stored
as a ``dict`` on the ``ExifField``.
Each exif information of the dictionary consists of two keys:

* ``desc``: A human readable description
* ``val``: The value for the entry.

In the following example we access the camera model ::

   image = Image.objects.get(...)
   print(image.exif['Model'])
   # {
   #     'desc': 'Camera Model Name',
   #     'val': 'DMC-GX7',
   # }

As the exif information is encoded in a simple ``dict`` you can iterate and access
the values with all familiar dictionary methods.


Denormalizing Fields
--------------------

Since the ``ExifField`` stores its data simply as text, it is not possible to filter
or access indiviual values efficiently.
The ``ExifField`` provides a convinient way to denormalize certain values using
the ``denormalized_fields`` argument.
It takes a dictionary with the target field as key and a simple getter function of
type ``Callable[[Dict[Dict[str, str]]], Any]``.
To denormalize a simple value you can use the provided ``exiffield.getters.exifgetter`` ::


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


There are more predefined getters in ``exiffield.getters``:

``exifgetter(exif_key: str) -> str``
    Get an unmodified exif value.

``get_type() -> str``
    Get file type, e.g. video or image

``get_datetake -> Optional[datetime]``
    Get when the file was created as ``datetime``

``get_orientation  -> exiffield.getters.Orientation``
    Get orientation of media file.
    Possible values are ``LANDSCAPE`` and ``PORTRAIT``.

``get_sequenctype -> exiffield.getters.Mode``
    Guess if the image was taken in a sequence.
    Possible values are ``BURST``, ``BRACKETING``, ``TIMELAPSE`` and ``SINGLE``.

``get_sequencenumber -> int``
    Get image position in a sequence.


Development
===========

This project is using `poetry <https://poetry.eustace.io/>`_ to manage all dev dependencies.
Clone this repository and run ::

   poetry develop


to create a virtual enviroment with all dependencies.
You can now run the test suite using ::

   poetry run pytest


This repository follows the `angular commit conventions <https://github.com/marionebl/commitlint/tree/master/@commitlint/config-angular>`_.
You can register a pre-commit hook to validate your commit messages by using
`husky <https://github.com/typicode/husky>`_. The configurations are already in place if
you have nodejs installed. Just run ::

   npm install

and the pre-commit hook will be registered.
