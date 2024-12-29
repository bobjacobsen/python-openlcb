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
