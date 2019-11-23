from django.db import models

from exiffield.fields import ExifField
from exiffield.getters import exifgetter


class Image(models.Model):
    image = models.ImageField()
    camera = models.CharField(editable=False, max_length=100,)
    exif = ExifField(
        source='image', denormalized_fields={'camera': exifgetter('Model')},
    )

    class Meta:
        app_label = 'tests'
