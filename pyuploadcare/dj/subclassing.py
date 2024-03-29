"""
Convenience routines for creating non-trivial Field subclasses, as well as
backwards compatibility utilities.

Add SubfieldBase as the metaclass for your Field subclass, implement
to_python() and the other necessary methods and everything will work
seamlessly.

Starts with the Django1.8 this code is deprecated and will be removed from
further releases. Because of this we move this code to us directly (clearing
it from deprecation warnings).

Original code: https://github.com/django/django/blob/1.9.1/django/db/models/fields/subclassing.py
An issue for more explanation: https://github.com/uploadcare/pyuploadcare/issues/94
"""


class SubfieldBase(type):
    """
    A metaclass for custom Field subclasses. This ensures the model's attribute
    has the descriptor protocol attached to it.
    """

    def __new__(cls, name, bases, attrs):
        new_class = super(SubfieldBase, cls).__new__(cls, name, bases, attrs)
        new_class.contribute_to_class = make_contrib(  # type: ignore[attr-defined]
            new_class, attrs.get("contribute_to_class")
        )
        return new_class


class Creator:
    """
    A placeholder class that provides a way to set the attribute on the model.
    """

    def __init__(self, field):
        self.field = field

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return obj.__dict__[self.field.name]

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = self.field.to_python(value)


def make_contrib(superclass, func=None):
    """
    Returns a suitable contribute_to_class() method for the Field subclass.

    If 'func' is passed in, it is the existing contribute_to_class() method on
    the subclass and it is called before anything else. It is assumed in this
    case that the existing contribute_to_class() calls all the necessary
    superclass methods.
    """

    def contribute_to_class(self, cls, name, **kwargs):
        if func:
            func(self, cls, name, **kwargs)
        else:
            super(superclass, self).contribute_to_class(cls, name, **kwargs)
        setattr(cls, self.name, Creator(self))

    return contribute_to_class
