from pyuploadcare.ucare_cli.main import ucare_argparser


def arg_namespace(arguments):
    """Parse CLI arguments given as a string or as an already split list.

    A list is needed for values that contain whitespace or a leading dash.
    """
    if isinstance(arguments, str):
        arguments = arguments.split()

    return ucare_argparser().parse_args(arguments)
