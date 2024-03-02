# coding: utf-8
from __future__ import unicode_literals

from typing import Any, Dict
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.forms import Field, TextInput
from django.template.loader import render_to_string
from django.templatetags.static import static

from pyuploadcare.client import Uploadcare
from pyuploadcare.dj.client import get_uploadcare_client
from pyuploadcare.dj.conf import (
    config,
    get_legacy_widget_js_url,
    get_widget_css_url,
    get_widget_js_url,
    user_agent_extension,
    user_agent_extension_short,
)
from pyuploadcare.exceptions import InvalidRequestError


class LegacyFileWidget(TextInput):
    """Django form widget that sets up Uploadcare Widget.

    It adds js and hidden input with basic Widget's params, e.g.
    *data-public-key*.

    """

    input_type = "hidden"
    is_hidden = False

    class Media:
        js = (get_legacy_widget_js_url(),)

    def __init__(self, attrs=None):
        default_attrs = {
            "role": "uploadcare-uploader",
            "data-public-key": config["pub_key"],
            "data-integration": user_agent_extension,
        }

        if config["upload_base_url"] is not None:
            default_attrs["data-url-base"] = config["upload_base_url"]

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

    def _widget_options(self, attrs=None) -> Dict[str, Any]:
        options: Dict[str, Any] = {
            "multiple": False,
            "user-agent-integration": user_agent_extension_short,
        }

        if config["cdn_base"] is not None:
            options["cdn-cname"] = config["cdn_base"]

        if config["upload_base_url"] is not None:
            options["base-url"] = config["upload_base_url"]

        options.update(config["widget"]["options"])
        options.update(self.attrs)
        if attrs:
            options.update(attrs)

        # Convert True, False to "true", "false"
        options = {
            k: str(v).lower() if isinstance(v, bool) else v
            for k, v in options.items()
            if k not in ["class"]
        }

        return options

    def render(self, name, value, attrs=None, renderer=None):
        variant = config["widget"]["variant"]

        uploadcare_js = get_widget_js_url()
        uploadcare_css = get_widget_css_url(variant)

        # If assets are locally served, use STATIC_URL to prefix their URLs
        if not urlparse(uploadcare_js).netloc:
            uploadcare_js = static(uploadcare_js)
        if not urlparse(uploadcare_css).netloc:
            uploadcare_css = static(uploadcare_css)

        widget_options = self._widget_options(attrs=attrs)

        return render_to_string(
            "uploadcare/forms/widgets/file.html",
            {
                "name": name,
                "value": value,
                "is_required": self.is_required,
                "options": widget_options,
                "pub_key": config["pub_key"],
                "variant": variant,
                "uploadcare_js": uploadcare_js,
                "uploadcare_css": uploadcare_css,
            },
        )


class FileField(Field):
    """Django form field that uses ``FileWidget`` with default arguments.

    It always returns URL.

    """

    widget = LegacyFileWidget if config["use_legacy_widget"] else FileWidget
    _client: Uploadcare

    def __init__(self, *args, **kwargs):
        self._client = get_uploadcare_client()

        super().__init__(*args, **kwargs)

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
        if config["signed_uploads"]:
            expire, signature = self._client.generate_upload_signature()
            attrs["data-secure-expire"] = str(expire)
            attrs["data-secure-signature"] = signature
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
            if self.manual_crop is not None:
                attrs["data-crop"] = self.manual_crop
        else:
            attrs["img-only"] = True
            attrs["use-cloud-image-editor"] = True
            if self.manual_crop is not None:
                attrs["crop-preset"] = self.manual_crop
        return attrs


class FileGroupField(Field):
    """Django form field that sets up ``FileWidget`` in multiupload mode."""

    widget = LegacyFileWidget if config["use_legacy_widget"] else FileWidget

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
        attrs: Dict[str, Any] = {}
        if self.legacy_widget:
            attrs["data-multiple"] = ""
            if not self.required:
                attrs["data-clearable"] = ""
        else:
            attrs["multiple"] = True
            attrs["group-output"] = True
            if self.required:
                attrs["multiple-min"] = 1
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
