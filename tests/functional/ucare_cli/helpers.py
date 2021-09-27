from pyuploadcare.ucare_cli.main import ucare_argparser


def arg_namespace(arguments_str):
    return ucare_argparser().parse_args(arguments_str.split())
