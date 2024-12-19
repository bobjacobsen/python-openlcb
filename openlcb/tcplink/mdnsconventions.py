from logging import getLogger

from openlcb import only_hex_pairs


logger = getLogger(__name__)


def id_from_tcp_service_name(service_name):
    """Scrape an MDNS TCP service name, assuming it uses conventions
    (`"{org}_{model}_{id}._openlcb-can.{protocol}.{tld}".format(...)`)
    Example:
    "bobjacobsen_pythonopenlcb_02015700049C._openlcb-can._tcp.local."
    becomes "02.01.57.00.04.9C"

    Args:
        service_name (str): A service name containing a 12-digit
            continuous string of digits, starting with "_" and ending
            with ".". (See also mdnsconventions.py)

    Returns:
        str: An LCC ID formatted as a human-readable string
            ("."-separated hex pairs), or None if no 12-digit number
            could be detected (See service_name).
    """
    lcc_id = None
    fqdn_parts = service_name.split(".")
    # if len(fqdn_parts) < 2:
    #     error = "less than 2 parts in {}".format(service_name)
    #     return None
    name_parts = fqdn_parts[0].split("_")
    msg = "No part has 12 hex digits (0-9, A-F)"
    for part in name_parts:
        if len(part) != 12:
            logger.debug("Not 12 characters: {}".format(repr(part)))
            continue
        msg = "No 12-character underscore-separated part, all hex"
        if not only_hex_pairs(part):
            logger.debug("Not hex digits: {}".format(repr(part)))
            continue
        sep = "."
        lcc_id = sep.join([part[i*2:i*2+2] for i in range(len(part)//2)])
        logger.debug("id_from_tcp_service_name got {}".format(repr(lcc_id)))
        msg = None

    if msg:
        logger.info(msg)
    return lcc_id
