from pyuploadcare.client import Uploadcare


def register_arguments(subparsers):
    subparser = subparsers.add_parser("delete_webhook", help="delete webhook")
    subparser.set_defaults(func=delete_webhook)
    subparser.add_argument("webhook_id", help="webhook id")
    return subparser


def delete_webhook(arg_namespace, client: Uploadcare):
    client.delete_webhook(arg_namespace.webhook_id)
