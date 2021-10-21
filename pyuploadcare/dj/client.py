from pyuploadcare.client import Uploadcare
from pyuploadcare.dj import conf as dj_conf


def get_uploadcare_client():
    config = {
        "public_key": dj_conf.pub_key,
        "secret_key": dj_conf.secret,
        "user_agent_extension": dj_conf.user_agent_extension,
    }

    if dj_conf.cdn_base:
        config["cdn_base"] = dj_conf.cdn_base

    if dj_conf.upload_base_url:
        config["upload_base"] = dj_conf.upload_base_url

    return Uploadcare(**config)
