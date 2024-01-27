import unittest

from linklayer import LinkLayer

from mti import MTI
from message import Message
from nodeid import NodeID

class TestLinkLayerClass(unittest.TestCase) :

    # test function marks that the listeners were fired
    received = False
    def receiveListener(self, msg) : self.received = True

    def testReceipt(self) :
        received = False
        msg = Message(MTI.Initialization_Complete,  NodeID(12), NodeID(21))
        receiver  = self.receiveListener
        layer = LinkLayer(NodeID(100))
        layer.registerMessageReceivedListener(receiver)
        
        layer.fireListeners(msg)
        
        self.assertTrue(self.received)

if __name__ == '__main__':
    unittest.main()
