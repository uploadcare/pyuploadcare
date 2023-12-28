import unittest

from pyuploadcare.dj.conf import (
    config,
    get_legacy_widget_js_url,
    get_widget_css_url,
    get_widget_js_url,
)


class GetLegacyWidgetAssetsTest(unittest.TestCase):
    def setUp(self):
        self._original_use_hosted_assets = config["use_hosted_assets"]
        self._original_legacy_widget = config["legacy_widget"]
        config["use_hosted_assets"] = True
        config["legacy_widget"] = {
            "version": "3.14",
            "build": "min",
            "override_js_url": None,
        }

    def tearDown(self):
        config["use_hosted_assets"] = self._original_use_hosted_assets
        config["legacy_widget"] = self._original_legacy_widget

    def test_hosted_js_url(self):
        config["use_hosted_assets"] = True
        self.assertEqual(
            get_legacy_widget_js_url(),
            "https://ucarecdn.com/libs/widget/3.14/uploadcare.min.js",
        )

    def test_local_js_url(self):
        config["use_hosted_assets"] = False
        self.assertEqual(
            get_legacy_widget_js_url(), "uploadcare/uploadcare.min.js"
        )

    def test_override_js_url(self):
        config["legacy_widget"][
            "override_js_url"
        ] = "https://example.com/uploadcare.js"
        self.assertEqual(
            get_legacy_widget_js_url(), "https://example.com/uploadcare.js"
        )


class GetWidgetAssetsTest(unittest.TestCase):
    def setUp(self):
        self._original_use_hosted_assets = config["use_hosted_assets"]
        self._original_widget = config["widget"]
        config["use_hosted_assets"] = True
        config["widget"] = {
            "version": "latest",
            "variant": "inline",
            "build": "",
            "options": {},
            "override_js_url": None,
            "override_css_url": {
                "regular": None,
                "inline": None,
                "minimal": None,
            },
        }

    def tearDown(self):
        config["use_hosted_assets"] = self._original_use_hosted_assets
        config["widget"] = self._original_widget

    def test_hosted_js_url(self):
        config["use_hosted_assets"] = True
        self.assertEqual(
            get_widget_js_url(),
            "https://cdn.jsdelivr.net/npm/@uploadcare/blocks@latest/web/blocks.js",
        )

    def test_local_js_url(self):
        config["use_hosted_assets"] = False
        self.assertEqual(get_widget_js_url(), "uploadcare/blocks.js")

    def test_override_js_url(self):
        config["widget"]["override_js_url"] = "https://example.com/blocks.js"
        self.assertEqual(get_widget_js_url(), "https://example.com/blocks.js")

    def test_hosted_css_url(self):
        config["use_hosted_assets"] = True
        self.assertEqual(
            get_widget_css_url("minimal"),
            "https://cdn.jsdelivr.net/npm/@uploadcare/blocks@latest"
            + "/web/lr-file-uploader-minimal.css",
        )

    def test_local_css_url(self):
        config["use_hosted_assets"] = False
        self.assertEqual(
            get_widget_css_url("minimal"),
            "uploadcare/lr-file-uploader-minimal.css",
        )

    def test_override_css_url(self):
        config["widget"]["override_css_url"][
            "minimal"
        ] = "https://example.com/minimal.css"
        self.assertEqual(
            get_widget_css_url("minimal"), "https://example.com/minimal.css"
        )
