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


django-exiffield extracts exif data by utilizing ``exiftool``.

Requirements
===========

- `exiftool <https://www.sno.phy.queensu.ca/~phil/exiftool/>`_
- Python 3.6
- Django >= 1.8


Installation
===========

#. Install django-exiffield ::

    pip install django-exiffield


Integration
===========

TODO...

Development
===========

This project is using `pipenv <https://docs.pipenv.org/>`_ to manage all dev dependencies.
Clone this repository and run ::

   pipenv install
   pipenv shell


to create and activet the required virtual enviroment with all dependencies.
You can now run the test suite using ::

   pytest


This repository follows the `angular commit conventions <https://github.com/marionebl/commitlint/tree/master/@commitlint/config-angular>`_.
You can register a pre-commit hook to validate your commit messages by using
`husky <https://github.com/typicode/husky>`_. The configurations are already in place if
you have nodejs installed. Just run ::

   npm install

and the pre-commit hook will be registered.
