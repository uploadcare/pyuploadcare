from django import forms
from pyuploadcare.dj.forms import ImageGroupField


class ImgForm(forms.Form):
    picImg = ImageGroupField(label='')
