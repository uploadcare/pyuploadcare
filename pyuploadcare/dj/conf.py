# coding: utf-8

import typing
from copy import deepcopy

import typing_extensions
from django import get_version as django_version
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from pyuploadcare import __version__ as library_version
from pyuploadcare.helpers import deep_update


__all__ = [
    "LegacyWidgetSettingsType",
    "WidgetSettingsType",
    "SettingsType",
    "config",
    "user_agent_extension",
    "user_agent_extension_short",
    "get_legacy_widget_js_url",
    "get_widget_js_url",
    "get_widget_css_url",
]

if not hasattr(settings, "UPLOADCARE"):
    raise ImproperlyConfigured("UPLOADCARE setting must be set")


WidgetVariantType = typing_extensions.Literal["regular", "inline", "minimal"]


class WidgetSettingsType(typing_extensions.TypedDict):
    version: str
    variant: WidgetVariantType
    build: str
    options: typing.Dict[str, typing.Any]
    override_js_url: typing.Optional[str]
    override_css_url: typing.Dict[WidgetVariantType, typing.Optional[str]]


class LegacyWidgetSettingsType(typing_extensions.TypedDict):
    version: str
    build: str
    override_js_url: typing.Optional[str]


class SettingsType(typing_extensions.TypedDict):
    pub_key: str
    secret: str
    cdn_base: typing.Optional[str]
    upload_base_url: typing.Optional[str]
    signed_uploads: bool
    use_legacy_widget: bool
    use_hosted_assets: bool
    widget: WidgetSettingsType
    legacy_widget: LegacyWidgetSettingsType


DEFAULT_CONFIG: SettingsType = {
    "pub_key": "",
    "secret": "",
    "cdn_base": None,
    "upload_base_url": None,
    "signed_uploads": False,
    "use_legacy_widget": False,
    "use_hosted_assets": True,
    "widget": {
        "version": "1",
        "variant": "regular",
        "build": "min",
        "options": {},
        "override_js_url": None,
        "override_css_url": {
            "regular": None,
            "inline": None,
            "minimal": None,
        },
    },
    "legacy_widget": {
        "version": "3.x",
        "build": "full.min",
        "override_js_url": None,
    },
}

_config = deepcopy(DEFAULT_CONFIG)
_config = deep_update(_config, settings.UPLOADCARE)  # type: ignore

config: SettingsType = typing.cast(SettingsType, _config)

if not config["pub_key"]:
    raise ImproperlyConfigured("UPLOADCARE setting must have pub_key")
if not config["secret"]:
    raise ImproperlyConfigured("UPLOADCARE setting must have secret")


user_agent_extension = "Django/{0}; PyUploadcare-Django/{1}".format(
    django_version(), library_version
)

user_agent_extension_short = "PyUploadcare-Django/{0}".format(library_version)

# Legacy widget (uploadcare.js)


def get_legacy_widget_js_url() -> str:
    widget_config = config["legacy_widget"]
    filename = "uploadcare.{0}.js".format(widget_config["build"]).replace(
        "..", "."
    )
    hosted_url = (
        "https://ucarecdn.com/libs/widget/{version}/{filename}".format(
            version=widget_config["version"], filename=filename
        )
    )
    local_url = "uploadcare/{filename}".format(filename=filename)
    override_url = widget_config["override_js_url"]

    if override_url:
        return override_url
    elif config["use_hosted_assets"]:
        return hosted_url
    else:
        return local_url


# New widget (blocks.js)


def get_widget_js_url() -> str:
    widget_config = config["widget"]
    filename = "file-uploader.{0}.min.js".format(
        widget_config["build"]
    ).replace("..", ".")
    hosted_url = (
        "https://cdn.jsdelivr.net/npm/@uploadcare/file-uploader@{version}"
        + "/web/{filename}"
    ).format(version=widget_config["version"], filename=filename)
    local_url = "uploadcare/{filename}".format(filename=filename)
    override_url = widget_config["override_js_url"]
    if override_url:
        return override_url
    elif config["use_hosted_assets"]:
        return hosted_url
    else:
        return local_url


def get_widget_css_url(variant: WidgetVariantType) -> str:
    widget_config = config["widget"]
    filename = "uc-file-uploader-{0}.{1}.min.css".format(
        variant, widget_config["build"]
    ).replace("..", ".")
    hosted_url = (
        "https://cdn.jsdelivr.net/npm/@uploadcare/file-uploader@{version}"
        + "/web/{filename}"
    ).format(version=widget_config["version"], filename=filename)
    local_url = "uploadcare/{filename}".format(filename=filename)
    override_url = widget_config["override_css_url"][variant]
    if override_url:
        return override_url
    elif config["use_hosted_assets"]:
        return hosted_url
    else:
        return local_url
