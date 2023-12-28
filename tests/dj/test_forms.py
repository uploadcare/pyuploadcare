# coding: utf-8
from __future__ import unicode_literals

import unittest

from django import forms
from django.core.exceptions import ValidationError

from pyuploadcare.dj import forms as uc_forms
from pyuploadcare.dj.conf import config


class FormFieldsAttributesTest(unittest.TestCase):
    def setUp(self):
        self._original_pub_key = config["pub_key"]
        self._original_secret = config["secret"]
        config["pub_key"] = "asdf"
        config["secret"] = "qwer"

    def tearDown(self):
        config["pub_key"] = self._original_pub_key
        config["secret"] = self._original_secret

    def test_legacy_default_form_field(self):
        class SomeForm(forms.Form):
            cf = forms.CharField()
            ff = uc_forms.FileField(widget=uc_forms.LegacyFileWidget)

        f = SomeForm(label_suffix="")
        self.assertTrue(f["ff"].field.legacy_widget)
        self.assertRegex(
            str(f.media),
            r"https://ucarecdn\.com/libs/widget/[\d\.x]+/uploadcare\.full.min\.js",
        )
        self.assertIn('role="uploadcare-uploader"', str(f["ff"]))
        self.assertIn('data-public-key="asdf"', str(f["ff"]))
        self.assertIn('type="hidden"', str(f["ff"]))

    def test_default_form_field(self):
        class SomeForm(forms.Form):
            cf = forms.CharField()
            ff = uc_forms.FileField()

        f = SomeForm(label_suffix="")
        self.assertFalse(f["ff"].field.legacy_widget)
        ff_str = str(f["ff"])
        self.assertIn("LR.registerBlocks(LR);", ff_str)
        self.assertIn("<lr-config\n", ff_str)
        self.assertIn('pubkey="asdf"', ff_str)
        self.assertIn('ctx-name="ff"', ff_str)

    def test_legacy_form_field_custom_attrs(self):
        class SomeForm(forms.Form):
            cf = forms.CharField()
            ff = uc_forms.FileField(
                widget=uc_forms.LegacyFileWidget(attrs={"role": "role"})
            )

        f = SomeForm(label_suffix="")
        self.assertRegex(
            str(f.media),
            r"https://ucarecdn\.com/libs/widget/[\d\.x]+/uploadcare\.full\.min\.js",
        )
        self.assertIn('role="role"', str(f["ff"]))
        self.assertIn('data-public-key="asdf"', str(f["ff"]))
        self.assertIn('type="hidden"', str(f["ff"]))

    def test_form_field_custom_attrs(self):
        class SomeForm(forms.Form):
            cf = forms.CharField()
            ff = uc_forms.FileField(
                widget=uc_forms.FileWidget(attrs={"source-list": "local"})
            )

        f = SomeForm(label_suffix="")
        self.assertFalse(f["ff"].field.legacy_widget)
        ff_str = str(f["ff"])
        self.assertIn("LR.registerBlocks(LR);", ff_str)
        self.assertIn('source-list="local"', ff_str)


class FileFieldURLTest(unittest.TestCase):
    def test_returns_url_if_uuid_is_given(self):
        cdn_url = uc_forms.FileField().clean(
            "cde35b21-c5e1-4ed4-b2fc-d4ef4b0538b0"
        )
        expected_cdn_url = (
            "https://ucarecdn.com/cde35b21-c5e1-4ed4-b2fc-d4ef4b0538b0/"
        )

        self.assertEqual(cdn_url, expected_cdn_url)

    def test_returns_url_if_url_has_aleady_been_given(self):
        cdn_url = uc_forms.FileField().clean(
            "www.ucarecdn.com/cde35b21-c5e1-4ed4-b2fc-d4ef4b0538b0"
        )
        expected_cdn_url = (
            "https://ucarecdn.com/cde35b21-c5e1-4ed4-b2fc-d4ef4b0538b0/"
        )

        self.assertEqual(cdn_url, expected_cdn_url)

    def test_raises_exc_if_value_is_invalid(self):
        with self.assertRaises(ValidationError):
            uc_forms.FileField().clean("blah")

    def test_empty_values_are_allowed(self):
        file_field = uc_forms.FileField(required=False)

        self.assertEqual(file_field.clean(""), "")
        self.assertIsNone(file_field.clean(None))


class FileGroupFieldURLTest(unittest.TestCase):
    def test_returns_url_if_uuid_is_given(self):
        cdn_url = uc_forms.FileGroupField().clean(
            "0513dda0-582f-447d-846f-096e5df9e2bb~2"
        )
        expected_cdn_url = (
            "https://ucarecdn.com/0513dda0-582f-447d-846f-096e5df9e2bb~2/"
        )

        self.assertEqual(cdn_url, expected_cdn_url)

    def test_returns_url_if_url_has_aleady_been_given(self):
        cdn_url = uc_forms.FileGroupField().clean(
            "ucarecdn.com/0513dda0-582f-447d-846f-096e5df9e2bb~2/"
        )
        expected_cdn_url = (
            "https://ucarecdn.com/0513dda0-582f-447d-846f-096e5df9e2bb~2/"
        )

        self.assertEqual(cdn_url, expected_cdn_url)

    def test_raises_exc_if_value_is_invalid(self):
        with self.assertRaises(ValidationError):
            uc_forms.FileGroupField().clean("blah")

    def test_empty_values_are_allowed(self):
        file_group_field = uc_forms.FileGroupField(required=False)

        self.assertEqual(file_group_field.clean(""), "")
        self.assertIsNone(file_group_field.clean(None))
