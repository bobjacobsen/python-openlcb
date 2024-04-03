import unittest

from openlcb.remotenodeprocessor import RemoteNodeProcessor

from openlcb.canbus.canlink import CanLink
from openlcb.eventid import EventID
from openlcb.node import Node
from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.pip import PIP


class TesRemoteNodeProcessorClass(unittest.TestCase):

    def setUp(self) :
        self.node21 = Node(NodeID(21))
        self.processor = RemoteNodeProcessor(CanLink(NodeID(100)))

    def testInitializationComplete(self) :
        # not related to node
        msg1 = Message(MTI.Initialization_Complete, NodeID(13), None)
        self.assertEqual(self.node21.state, Node.State.Uninitialized,
                         "node state starts uninitialized")
        self.processor.process(msg1, self.node21)
        self.assertEqual(self.node21.state, Node.State.Uninitialized,
                         "node state stays uninitialized")

        # send by node
        msg2 = Message(MTI.Initialization_Complete, NodeID(21), None)
        self.assertEqual(self.node21.state, Node.State.Uninitialized,
                         "node state starts uninitialized")
        self.processor.process(msg2, self.node21)
        self.assertEqual(self.node21.state, Node.State.Initialized,
                         "node state goes initialized")

    def testPipReplyFull(self) :
        msg1 = Message(MTI.Protocol_Support_Reply, NodeID(12), NodeID(13),
                       [0x10, 0x10, 0x00, 0x00])
        self.processor.process(msg1, self.node21)
        self.assertEqual(self.node21.pipSet, set(()))

        msg2 = Message(MTI.Protocol_Support_Reply, NodeID(21), NodeID(12),
                       [0x10, 0x10, 0x00, 0x00])
        self.processor.process(msg2, self.node21)
        self.assertEqual(self.node21.pipSet,
                         set([PIP.MEMORY_CONFIGURATION_PROTOCOL,
                              PIP.SIMPLE_NODE_IDENTIFICATION_PROTOCOL]))

    def testPipReply2(self) :
        msg1 = Message(MTI.Protocol_Support_Reply, NodeID(12), NodeID(13),
                       [0x10, 0x10])
        self.processor.process(msg1, self.node21)
        self.assertEqual(self.node21.pipSet, set(()))

        msg2 = Message(MTI.Protocol_Support_Reply, NodeID(21), NodeID(12),
                       [0x10, 0x10])
        self.processor.process(msg2, self.node21)
        self.assertEqual(self.node21.pipSet,
                         set([PIP.MEMORY_CONFIGURATION_PROTOCOL,
                              PIP.SIMPLE_NODE_IDENTIFICATION_PROTOCOL]))

    def testPipReplyEmpty(self) :
        msg = Message(MTI.Protocol_Support_Reply, NodeID(12), NodeID(13))
        self.processor.process(msg, self.node21)
        self.assertEqual(self.node21.pipSet, set(()))

    def testLinkDown(self) :
        self.node21.pipSet = set([PIP.EVENT_EXCHANGE_PROTOCOL])
        self.node21.state = Node.State.Initialized
        msg = Message(MTI.Link_Layer_Down, NodeID(0), NodeID(0))
        self.processor.process(msg, self.node21)
        self.assertEqual(self.node21.pipSet,
                         set([PIP.EVENT_EXCHANGE_PROTOCOL]))
        self.assertEqual(self.node21.state, Node.State.Uninitialized)

    def testLinkUp(self) :
        self.node21.pipSet = set([PIP.EVENT_EXCHANGE_PROTOCOL])
        self.node21.state = Node.State.Initialized
        msg = Message(MTI.Link_Layer_Up, NodeID(0), NodeID(0))
        self.processor.process(msg, self.node21)
        self.assertEqual(self.node21.pipSet,
                         set([PIP.EVENT_EXCHANGE_PROTOCOL]))
        self.assertEqual(self.node21.state, Node.State.Uninitialized)

    def testUndefinedType(self) :
        msg = Message(MTI.Unknown, NodeID(12), NodeID(13))  # neither to nor from us
        # nothing but logging happens on an unknown type
        self.processor.process(msg, self.node21)

        msg = Message(MTI.Unknown, NodeID(12), NodeID(21))  # to us
        # nothing but logging happens on an unknown type
        self.processor.process(msg, self.node21)

    def testSnipHandling(self) :
        self.node21.snip.manufacturerName = "name present"

        # message not to us
        msg = Message(MTI.Simple_Node_Ident_Info_Request, NodeID(12),
                      NodeID(13))
        self.processor.process(msg, self.node21)

        # should not have cleared SNIP and cache
        self.assertEqual(self.node21.snip.manufacturerName, "name present")

        # message to us
        msg = Message(MTI.Simple_Node_Ident_Info_Request, NodeID(12),
                      NodeID(21))
        self.processor.process(msg, self.node21)

        # should have cleared SNIP and cache
        self.assertEqual(self.node21.snip.manufacturerName, "")

        # add some data
        msg = Message(MTI.Simple_Node_Ident_Info_Reply, NodeID(21), NodeID(12),
                      [4, 0x31, 0x32, 0, 0, 0])
        self.processor.process(msg, self.node21)

        self.assertEqual(self.node21.snip.manufacturerName, "12")

    def testProducerIdentified(self) :
        self.node21.state = Node.State.Initialized
        msg = Message(MTI.Producer_Identified_Active, self.node21.id, None,
                      [1, 2, 3, 4, 5, 6, 7, 8])
        self.processor.process(msg, self.node21)
        self.assertTrue(self.node21.events.isProduced(
            EventID(0x01_02_03_04_05_06_07_08)
        ))

    def testProducerIdentifiedDifferentNode(self) :
        self.node21.state = Node.State.Initialized
        msg = Message(MTI.Producer_Identified_Active, NodeID(1), None,
                      [1, 2, 3, 4, 5, 6, 7, 8])
        self.processor.process(msg, self.node21)
        self.assertFalse(self.node21.events.isProduced(
            EventID(0x01_02_03_04_05_06_07_08)
        ))

    def testConsumerIdentified(self) :
        self.node21.state = Node.State.Initialized
        msg = Message(MTI.Consumer_Identified_Active, self.node21.id, None,
                      [1, 2, 3, 4, 5, 6, 7, 8])
        self.processor.process(msg, self.node21)
        self.assertTrue(self.node21.events.isConsumed(
            EventID(0x01_02_03_04_05_06_07_08)
        ))

    def testConsumerIdentifiedDifferentNode(self) :
        self.node21.state = Node.State.Initialized
        msg = Message(MTI.Consumer_Identified_Active, NodeID(1), None,
                      [1, 2, 3, 4, 5, 6, 7, 8])
        self.processor.process(msg, self.node21)
        self.assertFalse(self.node21.events.isConsumed(
            EventID(0x01_02_03_04_05_06_07_08)
        ))

    def testNewNodeSeen(self) :
        self.node21.state = Node.State.Initialized
        msg = Message(MTI.New_Node_Seen, NodeID(21), [])
        self.processor.process(msg, self.node21)


if __name__ == '__main__':
    unittest.main()
