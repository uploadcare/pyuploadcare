from pyuploadcare.client import Uploadcare
from pyuploadcare.ucare_cli.commands.helpers import pprint


def register_arguments(subparsers):
    subparser = subparsers.add_parser(
        "update_webhook", help="update a webhook"
    )
    subparser.set_defaults(func=update_webhook)
    subparser.add_argument("webhook_id", help="webhook id")
    subparser.add_argument("--target_url", help="webhook target URL")
    subparser.add_argument("--activate", action="store_true")
    subparser.add_argument("--deactivate", action="store_true")
    subparser.add_argument("--event")
    subparser.add_argument(
        "--signing_secret",
        help=(
            "Optional secret that, if set, will be used to calculate "
            "signatures for the webhook payloads sent to the target_url."
        ),
    )
    return subparser


def update_webhook(arg_namespace, client: Uploadcare):  # noqa: C901
    kwargs = {}

    if arg_namespace.target_url is not None:
        kwargs["target_url"] = arg_namespace.target_url

    if arg_namespace.activate:
        kwargs["is_active"] = True
    elif arg_namespace.deactivate:
        kwargs["is_active"] = False

    if arg_namespace.event is not None:
        kwargs["event"] = arg_namespace.event

    if arg_namespace.signing_secret is not None:
        kwargs["signing_secret"] = arg_namespace.signing_secret

    webhook = client.update_webhook(
        webhook_id=arg_namespace.webhook_id, **kwargs
    )
    pprint(webhook.dict())
