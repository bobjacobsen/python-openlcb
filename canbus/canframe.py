from openlcb.nodeid import NodeID

class CanFrame :
    header = 0
    data = []

    def __str__(self):
        return "CanFrame header: 0x{:08X} {}".format(self.header, self.data)

    # there are three ctor forms

    def __init__(self, arg1, arg2, arg3=[]) :
        # three arguments as N_cid, nodeID, alias
        if isinstance(arg2, NodeID) :
            # cid must be 4 to 7 inclusive
            # precondition(4 <= cid && cid <= 7)
            cid = arg1
            nodeID = arg2
            alias = arg3

            nodeCode = ( ( nodeID.nodeId >> ((cid-4)*12) ) & 0xFFF )
            self.header = ((cid << 12) | nodeCode) << 12 | (alias & 0xFFF) | 0x10_000_000
            self.data = []

        # two arguments as header, data
        elif isinstance(arg2, list) :
            self.header = arg1
            self.data = arg2

        # three arguments as control, alias, data
        elif isinstance(arg2, int) :
            control = arg1
            alias = arg2
            self.header = (control << 12) | (alias & 0xFFF) | 0x10_000_000
            self.data = arg3

        else:
            print("could not decode NodeID ctor arguments")

    def __eq__(self, other):
        if other is None : return False

        if self.header != other.header:
            return False
        if self.data != other.data:
            return False
        return True
