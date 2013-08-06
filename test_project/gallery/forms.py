# coding: utf-8
from django import forms
from pyuploadcare.dj.forms import ImageField

from .models import LocalPhoto


class MyForm(forms.ModelForm):

    uc_uuid = ImageField(manual_crop='2:3', label=u'Image')

    class Meta:
        model = LocalPhoto
        fields = ('uc_uuid',)
