from django.db import models

from pyuploadcare.dj import FileField, ImageField


class Photo(models.Model):
    title = models.CharField(max_length=255)
    photo = FileField()
    photo_2x3 = ImageField(manual_crop='2:3')

    def __unicode__(self):
        return self.title
