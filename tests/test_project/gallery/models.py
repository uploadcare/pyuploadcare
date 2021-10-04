from django.db import models

from pyuploadcare.dj.models import FileField, ImageField, ImageGroupField


class Gallery(models.Model):

    title = models.CharField(max_length=255)

    def __unicode__(self):
        return self.title


class Photo(models.Model):

    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    arbitrary_file = FileField(blank=True, null=True)
    photo_2x3 = ImageField(manual_crop="2:3", blank=True)

    def __unicode__(self):
        return self.title


class GalleryMultiupload(models.Model):

    title = models.CharField(max_length=255)
    photos = ImageGroupField()

    def __unicode__(self):
        return self.title
