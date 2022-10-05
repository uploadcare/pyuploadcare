def flatten_dict(simple_mapping, attribute_base="metadata") -> dict:
    """
    Straightforward way to use nested dict for multipart/form-data
    """
    result = dict()
    for key, val in simple_mapping.items():
        if not isinstance(val, str):
            raise TypeError(
                f"Expect 'string' for dict to be flatten, got {type(val)} instead"
            )
        result[f"{attribute_base}[{key}]"] = val

    return result
