from django.db import models

from pyuploadcare.dj import FileField


class Photo(models.Model):
    title = models.CharField(max_length=255)
    photo = FileField()

    def __unicode__(self):
        return self.title
