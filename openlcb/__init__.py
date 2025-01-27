from collections import OrderedDict
import re


hex_pairs_rc = re.compile(r"^([0-9A-Fa-f]{2})+$")
# {2}: Exactly two characters found (only match if pair)
# +: at least one match plus 0 or more additional matches


def only_hex_pairs(value):
    """Check if string contains only machine-readable hex pairs.
    See openlcb.conventions submodule for LCC ID dot notation
    functions (less restrictive).
    """
    return hex_pairs_rc.fullmatch(value)


def emit_cast(value):
    """Get type and value, such as for debug output."""
    repr_str = repr(value)
    if repr_str.startswith(type(value).__name__):
        return repr(value)  # type already included, such as bytearray(...)
    return "{}({})".format(type(value).__name__, repr_str)


def list_type_names(values):
    """Get the type of several values, such as for debug output.
    Args:
        values (Union[list,tuple,dict,OrderedDict]): A collection where
            each element's type is to be analyzed.
    Returns:
        list[str]: A list where each element is a type name. If
            values argument is dict-like, each element is formatted as
            "{key}: {type}".
    """
    if isinstance(values, (list, tuple)):
        return [type(value).__name__ for value in values]
    if isinstance(values, (dict, OrderedDict)):
        return ["{}: {}".format(k, type(v).__name__) for k, v in values.items()]
    raise TypeError("list_type_names is only implemented for"
                    " list, tuple, dict, and OrderedDict, but got a(n) {}"
                    .format(type(values).__name__))
