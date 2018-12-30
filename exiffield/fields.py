import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Generator, List

from django.core import checks, exceptions
from django.db import models
from django.db.models.fields.files import FieldFile
from django.db.models.signals import post_init, pre_save
from jsonfield import JSONField

from .exceptions import ExifError

logger = logging.getLogger(__name__)


def get_exif(file_: FieldFile) -> str:
    """
    Use exiftool to extract exif data from the given file field.
    """
    exiftool_path = shutil.which('exiftool')
    if not exiftool_path:
        raise ExifError('Could not find `exiftool`')

    if not file_._committed:
        # pipe file content to exiftool
        file_._file.seek(0)

        process = subprocess.run(
            [exiftool_path, '-j', '-l', '-'],
            check=True,
            input=file_._file.read(),
            stdout=subprocess.PIPE,
        )
        return process.stdout
    else:
        # pass physical file to exiftool
        file_path = file_.path
        return subprocess.check_output(
            [exiftool_path, '-j', '-l', file_path],
        )


class ExifField(JSONField):
    def __init__(self, *args, **kwargs) -> None:
        """
        Extract fields for denormalized exif values.
        """
        self.denormalized_fields = kwargs.pop('denormalized_fields', {})
        self.source = kwargs.pop('source', None)
        self.sync = kwargs.pop('sync', True)
        kwargs['editable'] = False
        kwargs['default'] = {}
        super().__init__(*args, **kwargs)

    def check(self, **kwargs) -> List[checks.CheckMessage]:
        """
        Check if current configuration is valid.
        """
        errors = super().check(**kwargs)
        if not self.model._meta.abstract:
            errors.extend(self._check_for_exiftool())
            errors.extend(self._check_fields())
            errors.extend(self._check_for_source())
        return errors

    def _check_for_exiftool(self) -> Generator[checks.CheckMessage, None, None]:
        """
        Return an error if `exiftool` is not available.
        """
        if not shutil.which('exiftool'):
            yield checks.Error(
                "`exiftool` not found.",
                hint="Please install `exiftool.`",
                obj=self,
                id='exiffield.E001',
            )

    def _check_for_source(self) -> Generator[checks.CheckMessage, None, None]:
        """
        Return errors if the source field is invalid.
        """
        if not self.source:
            yield checks.Error(
                f"`self.source` not set on {self.name}.",
                hint="Set `self.source` to an existing FileField.",
                obj=self,
                id='exiffield.E002',
            )
            return

        # check wether field is valid
        try:
            field = self.model._meta.get_field(self.source)
        except exceptions.FieldDoesNotExist:
            yield checks.Error(
                f"`{self.source}` not found on {self.model}.",
                hint="Check spelling or add field to model.",
                obj=self,
                id='exiffield.E003',
            )
            return
        if not isinstance(field, models.FileField):
            yield checks.Error(
                f"`{self.source}` on {self.model} must be a FileField.",
                obj=self,
                id='exiffield.E004',
            )

    def _check_fields(self) -> Generator[checks.CheckMessage, None, None]:
        """
        Return errors if any denormalized field is editable.
        python out loud
        """
        if not isinstance(self.denormalized_fields, dict):
            yield checks.Error(
                f"`denormalized_fields` on {self.model} should be a dictionary.",
                hint="Check the kwargs of `ExifField`",
                obj=self,
                id='exiffield.E005',
            )
            return

        for fieldname, func in self.denormalized_fields.items():
            try:
                field = self.model._meta.get_field(fieldname)
            except exceptions.FieldDoesNotExist:
                yield checks.Error(
                    f"`{fieldname}` not found on {self.model}.",
                    hint="Check spelling or add field to model.",
                    obj=self,
                    id='exiffield.E006',
                )
                continue

            if field.editable:
                yield checks.Error(
                    f"`{fieldname}` on {self.model} should not be editable.",
                    hint=f"Set `editable=False` on {fieldname}.",
                    obj=self,
                    id='exiffield.E007',
                )

            if not callable(func):
                yield checks.Error(
                    f"`Value for {fieldname}` on {self.model} should not be a callable.",
                    hint=f"Check your values for `denormalized_fields`",
                    obj=self,
                    id='exiffield.E008',
                )

    def contribute_to_class(
            self,
            cls: models.Model,
            name: str,
            **kwargs,
    ) -> None:
        """
        Register signals for retrieving and writing of exif data.
        """
        super().contribute_to_class(cls, name, **kwargs)

        # Only run post-initialization exif update on non-abstract models
        if not cls._meta.abstract:
            if self.sync:
                pre_save.connect(self.update_exif, sender=cls)

            # denormalize exif values
            pre_save.connect(self.denormalize_exif, sender=cls)
            post_init.connect(self.denormalize_exif, sender=cls)

    def denormalize_exif(
            self,
            instance: models.Model,
            **kwargs,
    ) -> None:
        """
        Update denormalized fields with new exif values.
        """
        exif_data = getattr(instance, self.name)
        if not exif_data:
            return

        for model_field, extract_from_exif in self.denormalized_fields.items():
            value = None
            try:
                value = extract_from_exif(exif_data)
            except Exception:
                logger.warning(
                    'Could not execute `%s` to extract value for `%s.%s`',
                    extract_from_exif.__name__,
                    instance.__class__.__name__, model_field,
                    exc_info=True,
                )
            if not value:
                continue

            setattr(instance, model_field, value)

    def update_exif(
            self,
            instance: models.Model,
            force: bool = False,
            commit: bool = False,
            **kwargs,
    ) -> None:
        """
        Load exif data from file.
        """
        file_ = getattr(instance, self.source)
        if not file_:
            # there is no file attached to the FileField
            return

        # check whether extraction of the exif is required
        exif_data = getattr(instance, self.name, None) or {}
        has_exif = bool(exif_data)
        filename = Path(file_.path).name
        exif_for_filename = exif_data.get('FileName', {}).get('val', '')
        file_changed = exif_for_filename != filename or not file_._committed

        if has_exif and not file_changed and not force:
            # nothing to do since the file has not been changed
            return

        try:
            exif_json = get_exif(file_)
        except Exception:
            logger.exception('Could not read metainformation from file: %s', file_.path)
            return

        try:
            exif_data = json.loads(exif_json)[0]
        except IndexError:
            return
        else:
            if 'FileName' not in exif_data:
                # If the file is uncommited, exiftool cannot extract a filenmae
                # We guess, that no other file with the same filename exists in
                # the storage.
                # In the worst case the exif is extracted twice...
                exif_data['FileName'] = {
                    'desc': 'Filename',
                    'val': filename,
                }
            setattr(instance, self.name, exif_data)

        if commit:
            instance.save()
