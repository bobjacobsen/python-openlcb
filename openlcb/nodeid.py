from openlcb import emit_cast


class NodeID:
    """A 6-byte (48-bit) Node ID.
    The constructor is manually overloaded as follows:
    - nodeId (int): If int.
    - nodeId (str): If str. Six dot-separated hex pairs.
    - nodeId (NodeID): If NodeID. data.nodeID is used in this case.
    - nodeId (bytearray): If bytearray (formerly list[int]). Six ints.

    Args:
        data (Union[int,str,NodeID,list[int]]): Node ID in int, dotted
            hex string, NodeID, or list[int] form.

    Attributes:
        nodeId (int): The node id in int form (uses 48 bits, so Python
            will allocate 64-bit or larger int)
    """
    def __str__(self):
        '''Display in standard format'''
        c = self.toArray()
        return ("{:02X}.{:02X}.{:02X}.{:02X}.{:02X}.{:02X}"
                "".format(c[0], c[1], c[2], c[3], c[4], c[5]))

    def __init__(self, data):
        # For args see class docstring.
        if isinstance(data, int):  # create from an integer value
            self.nodeId = data
        elif isinstance(data, str):
            parts = data.split(".")
            result = 0
            if len(parts) != 6:
                raise ValueError(
                    "6 dot-separated hex digits/pairs required if arg is str,"
                    " but got {}".format(emit_cast(data)))
            for part in parts:
                result = result*0x100+int(part, 16)
            self.nodeId = result
        elif isinstance(data, NodeID):
            self.nodeId = data.nodeId
        elif isinstance(data, bytearray):
            self.nodeId = 0
            if (len(data) > 0):
                self.nodeId |= (data[0] & 0xFF) << 40
            if (len(data) > 1):
                self.nodeId |= (data[1] & 0xFF) << 32
            if (len(data) > 2):
                self.nodeId |= (data[2] & 0xFF) << 24
            if (len(data) > 3):
                self.nodeId |= (data[3] & 0xFF) << 16
            if (len(data) > 4):
                self.nodeId |= (data[4] & 0xFF) << 8
            if (len(data) > 5):
                self.nodeId |= (data[5] & 0xFF)
        elif isinstance(data, list):
            print("invalid data type to nodeid constructor."
                  " Expected bytearray (formerly list[int])"
                  " unless int, str nor NodeID", data)
        else:
            print("invalid data type to nodeid constructor", data)

    def toArray(self):
        return bytearray([
            (self.nodeId >> 40) & 0xFF,
            (self.nodeId >> 32) & 0xFF,
            (self.nodeId >> 24) & 0xFF,
            (self.nodeId >> 16) & 0xFF,
            (self.nodeId >> 8) & 0xFF,
            (self.nodeId) & 0xFF
        ])

    def __eq__(self, other):
        if other is None:
            return False

        if self.nodeId != other.nodeId:
            return False
        return True

    def __hash__(self):
        return hash(self.nodeId)
