# making South happy
try:
    from south.modelsinspector import add_introspection_rules

    add_introspection_rules([], [r"^pyuploadcare\.dj\."])
except ImportError:
    pass
