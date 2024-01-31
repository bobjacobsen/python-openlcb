
import unittest

from openlcb.processor import Processor

from openlcb.node import Node
from openlcb.nodeid import NodeID
from openlcb.mti import MTI
from openlcb.message import Message


class TestStruct(Processor):
    def process(self, message, node):
        return False


class TestProcessorClass(unittest.TestCase):

    def testCheckSrcID(self):
        node1 = Node(NodeID(1))
        node2 = Node(NodeID(2))

        messageFrom1 = Message(MTI.Verified_NodeID, NodeID(1), None)

        put = TestStruct()

        self.assertTrue(put.checkSourceID(messageFrom1, node1))
        self.assertFalse(put.checkSourceID(messageFrom1, node2))

    def testCheckDestID(self):
        node1 = Node(NodeID(1))
        node2 = Node(NodeID(2))

        globalMessage = Message(MTI.Verified_NodeID, NodeID(1), None)
        addressedMessage = Message(MTI.Datagram, NodeID(1), NodeID(2))

        put = TestStruct()

        self.assertFalse(put.checkDestID(globalMessage, node1))
        self.assertTrue(put.checkDestID(addressedMessage, node2))
        self.assertFalse(put.checkDestID(globalMessage, node1))


if __name__ == '__main__':
    unittest.main()
