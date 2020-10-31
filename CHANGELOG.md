# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.0.0] - 2020-10-30

### Added

- Support remote storage, thanks to @jsutlovic

### Changed

- BREAKING: use [jsonfield](https://github.com/rpkilby/jsonfield) as field base as jsonfield2 is deprecated

## [2.1.0] - 2018-12-24

### Added

- Add django 2.2 and python 3.8 to tox
- Allow newer versions of pillow

## [2.0.0] - 2018-12-24

### Changed

- BREAKING: use [jsonfield2](https://pypi.org/project/jsonfield2/) as field base

### Fixed

- extract exif if file changed or exif information is missing

## [1.1.0] - 2018-12-04

### Changed

- change logging of exif denormalization to warning

## [1.0.1] - 2018-11-11

### Fixed

- fix `update_exif` with `commit=True`

## [1.0.0] 2018-09-26

### Added

- ability to extract exif from files which are not stored to the storage

### Changed

- poetry as build tool

## [0.1] - 2018-03-29

[Unreleased]: https://github.com/escaped/django-exiffield/compare/3.0.0...HEAD
[3.0.0]: https://github.com/escaped/django-exiffield/compare/2.1.0...3.0.0
[2.1.0]: https://github.com/escaped/django-exiffield/compare/2.0.0...2.1.0
[2.0.0]: https://github.com/escaped/django-exiffield/compare/1.1.0...2.0.0
[1.1.0]: https://github.com/escaped/django-exiffield/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/escaped/django-exiffield/compare/0.1...1.0.0
[0.1]: https://github.com/escaped/django-exiffield/tree/0.1
