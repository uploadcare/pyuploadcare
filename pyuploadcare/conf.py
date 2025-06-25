# coding: utf-8
"""
Configuration variables.

"""
import os

from pyuploadcare.helpers import get_cdn_base


# Do not import vars from this module.
# Instead import whole module and work with attributes.

__all__ = []


DEFAULT = object()
DEFAULT_API_BASE = "https://api.uploadcare.com/"
DEFAULT_UPLOAD_BASE = "https://upload.uploadcare.com/"
DEFAULT_CDN_BASE = "https://ucarecdn.com/"
DEFAULT_USE_SUBDOMAINS = "no"
DEFAULT_SUBDOMAIN_PATTERN = "https://{prefix}.ucarecd.net/"

pub_key = os.getenv("UPLOADCARE_PUBLIC_KEY")
secret = os.getenv("UPLOADCARE_SECRET_KEY")

api_version = "0.7"
api_base = os.getenv("UPLOADCARE_API_BASE", DEFAULT_API_BASE)
upload_base = os.getenv("UPLOADCARE_UPLOAD_BASE", DEFAULT_UPLOAD_BASE)
_forced_cdn_base = os.getenv("UPLOADCARE_CDN_BASE")

if _forced_cdn_base:
    cdn_base = _forced_cdn_base
else:
    # calculate cdn_base using current settings
    _use_subdomains = os.getenv(
        "UPLOADCARE_USE_SUBDOMAINS", DEFAULT_USE_SUBDOMAINS
    ).lower() in ("true", "yes")
    cdn_base = get_cdn_base(
        pub_key,
        default=DEFAULT_CDN_BASE,
        subdomains=_use_subdomains,
        subdomains_ptn=DEFAULT_SUBDOMAIN_PATTERN,
    )

signed_uploads = True
signed_uploads_ttl = 60

verify_api_ssl = True
verify_upload_ssl = True

timeout = DEFAULT

# retry throttled requests this many times
retry_throttled = 1

user_agent_extension = None

batch_chunk_size = 100

multipart_min_file_size = 10485760
multipart_chunk_size = 5 * 1024 * 1024
