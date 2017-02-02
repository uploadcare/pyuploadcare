from django import forms
from pyuploadcare.dj.forms import ImageGroupField
from pyuploadcare.dj.forms import ImageField


class ImgForm(forms.Form):
    picImg = ImageGroupField(label='')
