# coding: utf-8
"""
Configuration variables.

"""
import os


# Do not import vars from this module.
# Instead import whole module and work with attributes.

__all__ = []

DEFAULT = object()

pub_key = os.getenv("UPLOADCARE_PUBLIC_KEY")
secret = os.getenv("UPLOADCARE_SECRET_KEY")

api_version = "0.7"
api_base = os.getenv("UPLOADCARE_API_BASE", "https://api.uploadcare.com/")
upload_base = os.getenv(
    "UPLOADCARE_UPLOAD_BASE", "https://upload.uploadcare.com/"
)
cdn_base = os.getenv("UPLOADCARE_CDN_BASE", "https://ucarecdn.com/")
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
