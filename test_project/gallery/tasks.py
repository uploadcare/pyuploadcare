# coding: utf-8
import urllib2

from django.core.files.base import ContentFile
import celery
import pyuploadcare

from .models import LocalPhoto


@celery.task
def download_photo(local_photo_id, uc_uuid):
    local_photo = LocalPhoto.objects.get(pk=local_photo_id)
    uc_file = pyuploadcare.File(uc_uuid)

    content = urllib2.urlopen(uc_file.cdn_url).read()

    local_photo.photo.save(uc_file.filename(), ContentFile(content))
