import os
import unittest
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'

from django.core.exceptions import ValidationError
from pyuploadcare.dj.models import ImageField


class CropToolRegexTest(unittest.TestCase):

    def test_crop_tool_is_none(self):
        ImageField()

    def test_crop_tool_is_empty_str(self):
        ImageField("")

    def test_crop_tool_is_empty_unicode(self):
        ImageField(u"")

    def test_crop_tool_is_disabled(self):
        ImageField("disabled")

    def test_crop_tool_is_2colon3(self):
        ImageField("2:3")

    def test_crop_tool_is_200x300(self):
        ImageField("200x300")

    def test_crop_tool_is_200x300_upscale(self):
        ImageField("200x300 upscale")

    def test_validation_error_when_crop_tool_is_200colon300_upscale(self):
        self.assertRaises(ValidationError, ImageField, u"200:300 upscale")

    def test_validation_error_when_crop_tool_is_int(self):
        self.assertRaises(ValidationError, ImageField, 123)
