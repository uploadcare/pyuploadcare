from django.db import models

from pyuploadcare.dj import FileField

# Create your models here.
class Photo(models.Model):
    title = models.CharField(max_length=255)
    photo = FileField()
