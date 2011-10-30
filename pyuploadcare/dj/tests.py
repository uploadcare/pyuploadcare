import datetime

from django.test import TestCase
from django.conf import settings
from django import forms

from pyuploadcare.dj import forms as uc_forms

class TestFormFields(TestCase):
    def test_form_field(self):

        class SomeForm(forms.Form):
            cf = forms.CharField()
            ff = uc_forms.FileField()

        f = SomeForm()
        assert str(f).find('<input type="hidden" data-public-key="3aaee4d571b832736d722396bf541154f14aaa1f50e0199e374ba8edea84efb6"') != -1

        assert str(f.media).find('line-widget') != -1
