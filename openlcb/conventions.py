from logging import getLogger

from openlcb import only_hex_pairs

logger = getLogger(__name__)

LCC_ID_SEP = "."


def hex_to_dotted_lcc_id(hex_s):
    return LCC_ID_SEP.join([hex_s[i*2:i*2+2] for i in range(len(hex_s)//2)])


def validate_lcc_id(lcc_id_s):
    """Convert an LCC ID in dot notation to a hex and error pair.
    Get a tuple of a hex string and a validation error (or None)
    suitable for form validation (Done that way so this is the
    only function that does LCC ID analysis).

    Args:
        lcc_id_s (str): An LCC ID string. Examples: 02.01.57.00.04.9C or
            2.1.57.0.4.9C (both give same 12-digit hex string).

    Returns:
        tuple(str, str): tuple of hex string and error:
        - Hex string is 12 characters uppercase, or None if input is bad.
        - Error is only not None if hex string is None.
    """
    if not lcc_id_s:
        error = "[dotted_lcc_id_to_hex] Got {}".format(repr(lcc_id_s))
        # ^ repr shows '' or None
        return None, error
    parts = lcc_id_s.split(".")
    if len(parts) != 6:
        error = "Not 6 parts: {}".format(lcc_id_s)
        return None, error
    hex_s = ""
    for part in parts:
        if len(part) == 2:
            hex_s += part
        elif len(part) == 1:  # Add leading 0 since not required.
            hex_s += "0" + part
        elif len(part) < 1:
            error = "Extra '.' in {} (not an LCC ID)".format(repr(lcc_id_s))
            return None, error
        else:
            error = "Wrong length for {}".format(repr(part))
            return None, error
    if not only_hex_pairs(hex_s):
        error = "Non-hex found in {} (expected 0-9/A-F)".format(repr(lcc_id_s))
        return None, error
    return hex_s.upper(), None


def dotted_lcc_id_to_hex(lcc_id_s):
    hex_s, error = validate_lcc_id(lcc_id_s)
    if error:
        logger.info(error)
        return None
    return hex_s


def is_hex_lcc_id(value):
    """Check if it is a 12-character LCC ID in pure hex format.
    Uppercase or lowercase is valid if 12 characters. If dotted, you
    must first use dotted_lcc_id_to_hex to make it machine readable
    (including to add zero padding) or see if result is None from that
    before calling this.
    """
    # if (len(value) < 12) and (len(value) >= minimum_length):
    #     value = value.zfill(12)  # pad left with zeroes
    # ^ Commented since dotted_lcc_id_to_hex can be used to get
    #   a clean one if possible.
    if len(value) != 12:
        logger.info("Not 12 characters: {}".format(value))
        return False

    return only_hex_pairs(value)


def is_dotted_lcc_id(value):
    """It is an LCC ID in dot notation (human readable)
    Examples: 02.01.57.00.04.9C or 2.1.57.0.4.9C (same effect)

    To generate LCC IDs, first allocate a range at
    https://registry.openlcb.org/uniqueidranges
    """
    hex_str = dotted_lcc_id_to_hex(value)
    if not hex_str:  # warning/info logged by dotted_lcc_id_to_hex
        return False
    return only_hex_pairs(hex_str)
