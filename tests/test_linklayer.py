import unittest

from openlcb.linklayer import LinkLayer

from openlcb.mti import MTI
from openlcb.message import Message
from openlcb.nodeid import NodeID


class TestLinkLayerClass(unittest.TestCase):

    # test function marks that the listeners were fired
    received = False

    def receiveListener(self, msg):
        self.received = True

    def testReceipt(self):
        self.received = False
        msg = Message(MTI.Initialization_Complete, NodeID(12), NodeID(21))
        receiver = self.receiveListener
        layer = LinkLayer(NodeID(100))
        layer.registerMessageReceivedListener(receiver)

        layer.fireListeners(msg)

        self.assertTrue(self.received)


if __name__ == '__main__':
    unittest.main()
