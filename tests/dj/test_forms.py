# coding: utf-8
from __future__ import unicode_literals

import unittest

from django import forms
from django.core.exceptions import ValidationError

from pyuploadcare.dj import conf as dj_conf
from pyuploadcare.dj import forms as uc_forms


class FormFieldsAttributesTest(unittest.TestCase):
    def setUp(self):
        self._pub_key = dj_conf.pub_key
        self._secret = dj_conf.secret
        dj_conf.pub_key = "asdf"
        dj_conf.secret = "qwer"

    def tearDown(self):
        dj_conf.pub_key = self._pub_key
        dj_conf.secret = self._secret

    def test_default_form_field(self):
        class SomeForm(forms.Form):
            cf = forms.CharField()
            ff = uc_forms.FileField()

        f = SomeForm(label_suffix="")
        self.assertRegexpMatches(
            str(f.media),
            r"https://ucarecdn\.com/libs/widget/[\d\.x]+/uploadcare\.full.min\.js",
        )
        self.assertIn('role="uploadcare-uploader"', str(f["ff"]))
        self.assertIn('data-public-key="asdf"', str(f["ff"]))
        self.assertIn('type="hidden"', str(f["ff"]))

    def test_form_field_custom_attrs(self):
        class SomeForm(forms.Form):
            cf = forms.CharField()
            ff = uc_forms.FileField(
                widget=uc_forms.FileWidget(attrs={"role": "role"})
            )

        f = SomeForm(label_suffix="")
        self.assertRegexpMatches(
            str(f.media),
            r"https://ucarecdn\.com/libs/widget/[\d\.x]+/uploadcare\.full\.min\.js",
        )
        self.assertIn('role="role"', str(f["ff"]))
        self.assertIn('data-public-key="asdf"', str(f["ff"]))
        self.assertIn('type="hidden"', str(f["ff"]))


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
