
import unittest

from processor import *

from node import *
from nodeid import *
from mti import *
from message import *

class TestStruct(Processor) :
    def process(self, message, node) :
        return false

class TestProcessorClass(unittest.TestCase) :
    
    def testCheckSrcID(self) : 
        node1 = Node(NodeID(1))
        node2 = Node(NodeID(2))
        
        messageFrom1 = Message(MTI.Verified_NodeID, NodeID(1), None)
        
        put = TestStruct()
        
        self.assertTrue(put.checkSourceID(messageFrom1, node1))
        self.assertFalse(put.checkSourceID(messageFrom1, node2))

    def testCheckDestID(self) : 
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
