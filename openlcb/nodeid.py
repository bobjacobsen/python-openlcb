class NodeID:
    """Convert an integer, list, NodeID or string to a NodeID
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
            for part in parts:
                result = result*0x100+int(part, 16)
            self.nodeId = result
        elif isinstance(data, NodeID):
            self.nodeId = data.nodeId
        elif isinstance(data, list):
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
        else:
            print("invalid data type to nodeid constructor", data)

    def toArray(self):
        return [
            (self.nodeId >> 40) & 0xFF,
            (self.nodeId >> 32) & 0xFF,
            (self.nodeId >> 24) & 0xFF,
            (self.nodeId >> 16) & 0xFF,
            (self.nodeId >> 8) & 0xFF,
            (self.nodeId) & 0xFF
        ]

    def __eq__(self, other):
        if other is None:
            return False

        if self.nodeId != other.nodeId:
            return False
        return True

    def __hash__(self):
        return hash(self.nodeId)
