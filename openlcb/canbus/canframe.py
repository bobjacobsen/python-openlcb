from openlcb.nodeid import NodeID


class CanFrame:
    """OpenLCB-CAN frame
    Use CAN extended format (29-bit header)
    - However, operate error-free when network carries standard-format
      (11-bit header) frames.
    - Bit 28 of header is always sent as 1 and ignored upon receipt
       NOTE: 0x10_00_00_00 is bit 28 in hex.
    - See the "OpenLCB-CAN Frame Transfer" standard on openlcb.org for
      more details.

    Constructor arguments are manually overloaded as follows:
    - N_cid, nodeID, alias: If 2nd arg is NodeID.
    - header, data: If 2nd arg is list.
    - control, alias, data: If 2nd arg is int.

    Args:
        N_cid (int, optional): Frame sequence number (becomes first
            3 bits of 15-bit Check ID (CID) frame). 4 to 7 inclusive
            (for non-OpenLCB protocols, down to 1). See
            "OpenLCB-CAN Frame Transfer" standard or comments under
            "nodeCode" for how this affects nodeID bit field size.
        nodeID (NodeID, optional): (becomes last 12 bits at right
            side of Check ID (CID) frame, but which bits are used
            depends upon N_cid).
        alias (int, optional): Source NID Alias. A 12-bit version of the
            nodeID shortened using bitwise overlays, used as a local key
            for the device. See calls to createAlias12.
        header (int, optional): The entire 29-bit header already
            assembled (or received).
        data (list[int], optional): Payload
        control (int, optional): Frame type (1: OpenLCB = 0x0800_000,
            0: CAN Control Frame) | Content Field (3 bits, 3 nibbles,
            mask = 0x07FF_F000).
    """

    header = 0
    data = []

    def __str__(self):
        return "CanFrame header: 0x{:08X} {}".format(self.header, self.data)

    # there are three ctor forms

    def __init__(self, arg1, arg2, arg3=[]):
        # three arguments as N_cid, nodeID, alias
        if isinstance(arg2, NodeID):
            # cid must be 4 to 7 inclusive (100 to 111 binary)
            # precondition(4 <= cid && cid <= 7)
            cid = arg1
            nodeID = arg2
            alias = arg3

            nodeCode = ((nodeID.nodeId >> ((cid-4)*12)) & 0xFFF)
            # ^ cid-4 results in 0 to 3. *12 results in 0 to 36 bit shift (nodeID size)
            self.header = ((cid << 12) | nodeCode) << 12 | (alias & 0xFFF) | 0x10_00_00_00  # noqa: E501
            self.data = []

        # two arguments as header, data
        elif isinstance(arg2, list):
            self.header = arg1
            self.data = arg2

        # three arguments as control, alias, data
        elif isinstance(arg2, int):
            control = arg1
            alias = arg2
            self.header = (control << 12) | (alias & 0xFFF) | 0x10_00_00_00
            self.data = arg3
        else:
            print("could not decode NodeID ctor arguments")

    def __eq__(self, other):
        if other is None:
            return False

        if self.header != other.header:
            return False
        if self.data != other.data:
            return False
        return True
