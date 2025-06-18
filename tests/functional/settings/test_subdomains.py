import importlib
import sys
import os
import pytest


@pytest.mark.parametrize("use_subdomains,pub_key,expected_cdn_base", [
    (False, "demopublickey", "https://ucarecdn.com/"),
    (True, "demopublickey", "https://1s4oyld5dc.ucarecd.net/"),
    (True, "anotherkey", "https://4073mye3t0.ucarecd.net/"),
    (False, "anotherkey", "https://ucarecdn.com/"),
])
def test_cdn_base(tmp_path, use_subdomains, pub_key, expected_cdn_base):
    # patch
    os.environ["UPLOADCARE_PUBLIC_KEY"] = pub_key
    os.environ["UPLOADCARE_USE_SUBDOMAINS"] = str(use_subdomains)

    # reload conf
    if "pyuploadcare.conf" in sys.modules:
        del sys.modules["pyuploadcare.conf"]
    conf = importlib.import_module("pyuploadcare.conf")

    print(conf.pub_key, conf.use_subdomains, conf.cdn_base)
    cdn_base = conf.cdn_base
    assert cdn_base == expected_cdn_base

    # clean up
    del os.environ["UPLOADCARE_PUBLIC_KEY"]
    del os.environ["UPLOADCARE_USE_SUBDOMAINS"]
