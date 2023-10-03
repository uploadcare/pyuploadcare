# coding: utf-8
from __future__ import unicode_literals

from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.forms import Field, TextInput
from django.template.loader import render_to_string
from django.templatetags.static import static

from pyuploadcare.client import Uploadcare
from pyuploadcare.dj import conf as dj_conf
from pyuploadcare.dj.client import get_uploadcare_client
from pyuploadcare.exceptions import InvalidRequestError


class LegacyFileWidget(TextInput):
    """Django form widget that sets up Uploadcare Widget.

    It adds js and hidden input with basic Widget's params, e.g.
    *data-public-key*.

    """

    input_type = "hidden"
    is_hidden = False

    class Media:
        js = (dj_conf.legacy_uploadcare_js,)

    def __init__(self, attrs=None):
        default_attrs = {
            "role": "uploadcare-uploader",
            "data-public-key": dj_conf.pub_key,
        }

        if dj_conf.user_agent_extension is not None:
            default_attrs["data-integration"] = dj_conf.user_agent_extension

        if dj_conf.upload_base_url is not None:
            default_attrs["data-url-base"] = dj_conf.upload_base_url

        if attrs is not None:
            default_attrs.update(attrs)

        super(LegacyFileWidget, self).__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        return super(LegacyFileWidget, self).render(
            name, value, attrs, renderer
        )


class FileWidget(TextInput):
    _client: Uploadcare

    def __init__(self, attrs=None):
        self._client = get_uploadcare_client()
        super(FileWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        config = {
            "multiple": False,
        }

        if dj_conf.cdn_base:
            config.update(
                {
                    "cdnCname": dj_conf.cdn_base,
                }
            )

        config.update(dj_conf.widget_options)
        config.update(self.attrs)
        if attrs:
            config.update(attrs)

        # Convert True, False to "true", "false"
        config = {
            k: str(v).lower() if isinstance(v, bool) else v
            for k, v in config.items()
        }

        uploadcare_js = dj_conf.uploadcare_js
        uploadcare_css = dj_conf.uploadcare_css

        # If assets are locally served, use STATIC_URL to prefix their URLs
        if not urlparse(uploadcare_js).netloc:
            uploadcare_js = static(uploadcare_js)
        if not urlparse(uploadcare_css).netloc:
            uploadcare_css = static(uploadcare_css)

        return render_to_string(
            "uploadcare/forms/widgets/file.html",
            {
                "name": name,
                "value": value,
                "config": config,
                "pub_key": dj_conf.pub_key,
                "variant": dj_conf.widget_build,
                "uploadcare_js": uploadcare_js,
                "uploadcare_css": uploadcare_css,
            },
        )


class FileField(Field):
    """Django form field that uses ``FileWidget`` with default arguments.

    It always returns URL.

    """

    widget = LegacyFileWidget if dj_conf.legacy_widget else FileWidget
    _client: Uploadcare

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._client = get_uploadcare_client()

    def to_python(self, value):
        if value is None or value == "":
            return value

        try:
            return self._client.file(value).cdn_url
        except InvalidRequestError as exc:
            raise ValidationError(f"Invalid value for a field: {exc}")

    @property
    def legacy_widget(self) -> bool:
        return isinstance(self.widget, LegacyFileWidget)

    def widget_attrs(self, widget):
        attrs = {}
        if self.legacy_widget and not self.required:
            attrs["data-clearable"] = ""
        return attrs


class ImageField(FileField):
    """Django form field that sets up ``FileWidget`` to work with images."""

    def __init__(self, manual_crop=None, *args, **kwargs):
        self.manual_crop = manual_crop
        super(ImageField, self).__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super(ImageField, self).widget_attrs(widget)
        if self.legacy_widget:
            attrs["data-images-only"] = ""
        else:
            attrs["img-only"] = True
            attrs["use-cloud-image-editor"] = True
        if self.legacy_widget and self.manual_crop is not None:
            attrs["data-crop"] = self.manual_crop
        return attrs


class FileGroupField(Field):
    """Django form field that sets up ``FileWidget`` in multiupload mode."""

    widget = LegacyFileWidget if dj_conf.legacy_widget else FileWidget

    _client: Uploadcare

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._client = get_uploadcare_client()

    def to_python(self, value):
        if value is None or value == "":
            return value

        try:
            return self._client.file_group(value).cdn_url
        except InvalidRequestError as exc:
            raise ValidationError(f"Invalid value for a field: {exc}")

    @property
    def legacy_widget(self) -> bool:
        return isinstance(self.widget, LegacyFileWidget)

    def widget_attrs(self, widget):
        if self.legacy_widget:
            attrs = {"data-multiple": ""}
        else:
            attrs = {"multiple": True}
        if not self.required:
            attrs["data-clearable"] = ""
        return attrs


class ImageGroupField(FileGroupField):
    """Django form field that sets up ``FileWidget`` in image multiupload mode."""

    def widget_attrs(self, widget):
        attrs = super(ImageGroupField, self).widget_attrs(widget)
        if self.legacy_widget:
            attrs["data-images-only"] = ""
        else:
            attrs["img-only"] = True
        return attrs
