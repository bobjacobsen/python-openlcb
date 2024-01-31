import unittest

from openlcb.nodeid import NodeID
from openlcb.localnodeprocessor import LocalNodeProcessor
from openlcb.linklayer import LinkLayer
from openlcb.mti import MTI
from openlcb.message import Message
from openlcb.pip import PIP
from openlcb.node import Node
# from openlcb.processor import Processor


class LinkMockLayer(LinkLayer):
    sentMessages = []

    def sendMessage(self, message):
        LinkMockLayer.sentMessages.append(message)


class TestLocalNodeProcessorClass(unittest.TestCase):

    def setUp(self):
        self.node21 = Node(NodeID(21))
        LinkMockLayer.sentMessages = []
        self.processor = LocalNodeProcessor(LinkMockLayer(NodeID(100)))

    def testLinkUp(self):
        self.node21.state = Node.State.Uninitialized
        msg = Message(MTI.Link_Layer_Up, NodeID(0), NodeID(0), [])

        self.processor.process(msg, self.node21)

        self.assertEqual(self.node21.state, Node.State.Initialized)
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)
        self.assertEqual(LinkMockLayer.sentMessages[0],
                         Message(MTI.Initialization_Complete, self.node21.id,
                                 self.node21.id.toArray()))
        # self.assertEqual(LinkMockLayer.sentMessages[1],
        #     Message(MTI.Verify_NodeID_Number_Global, self.node21.id))

    def testLinkDown(self):
        self.node21.state = Node.State.Initialized
        msg = Message(MTI.Link_Layer_Down, NodeID(0), NodeID(0), [])

        self.processor.process(msg, self.node21)

        self.assertEqual(self.node21.state, Node.State.Uninitialized)
        self.assertEqual(len(LinkMockLayer.sentMessages), 0)

    def testVerifyGlobal(self):
        # not related to node
        msg1 = Message(MTI.Verify_NodeID_Number_Global, NodeID(13), None,
                       [0, 0, 0, 0, 12, 21])
        self.processor.process(msg1, self.node21)
        self.assertEqual(len(LinkMockLayer.sentMessages), 0)

        # global no node ID
        msg2 = Message(MTI.Verify_NodeID_Number_Global, NodeID(13), None)
        self.processor.process(msg2, self.node21)
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)
        LinkMockLayer.sentMessages = []

        # global this Node ID
        msg3 = Message(MTI.Verify_NodeID_Number_Global, NodeID(13), None,
                       [0, 0, 0, 0, 0, 21])
        self.processor.process(msg3, self.node21)
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)

    def testVerifyAddressed(self):
        # not related to node
        msg1 = Message(MTI.Verify_NodeID_Number_Addressed, NodeID(13),
                       NodeID(24), [0, 0, 0, 0, 0, 24])
        self.processor.process(msg1, self.node21)
        self.assertEqual(len(LinkMockLayer.sentMessages), 0)

        # addressed no node ID
        msg2 = Message(MTI.Verify_NodeID_Number_Addressed, NodeID(13),
                       NodeID(21))
        self.processor.process(msg2, self.node21)
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)
        LinkMockLayer.sentMessages = []

        # addressed this Node ID
        msg3 = Message(MTI.Verify_NodeID_Number_Addressed, NodeID(13),
                       NodeID(21), [0, 0, 0, 0, 0, 21])
        self.processor.process(msg3, self.node21)
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)

    def testPip(self):
        self.node21.pipSet = set([PIP.DATAGRAM_PROTOCOL,
                                  PIP.SIMPLE_NODE_IDENTIFICATION_PROTOCOL,
                                  PIP.EVENT_EXCHANGE_PROTOCOL])

        # not related to node
        msg1 = Message(MTI.Protocol_Support_Inquiry, NodeID(13), NodeID(24))
        self.processor.process(msg1, self.node21)
        self.assertEqual(len(LinkMockLayer.sentMessages), 0)

        # addressed to node
        msg2 = Message(MTI.Protocol_Support_Inquiry, NodeID(13), NodeID(21))
        self.processor.process(msg2, self.node21)
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)
        self.assertEqual(LinkMockLayer.sentMessages[0].data,
                         [0x44, 0x10, 0x00, 0x00, 0x00, 0x00])

    def testSnip(self):
        self.node21.snip.manufacturerName = "Sample Nodes"
        self.node21.snip.modelName = "Node 1"
        self.node21.snip.hardwareVersion = "HVersion 1"
        self.node21.snip.softwareVersion = "SVersion 1"
        self.node21.snip.updateSnipDataFromStrings()

        # not related to node
        msg1 = Message(MTI.Simple_Node_Ident_Info_Request, NodeID(13),
                       NodeID(24))
        self.processor.process(msg1, self.node21)
        self.assertEqual(len(LinkMockLayer.sentMessages), 0)

        # addressed to node
        msg2 = Message(MTI.Simple_Node_Ident_Info_Request, NodeID(13),
                       NodeID(21))
        self.processor.process(msg2, self.node21)
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)
        self.assertEqual(LinkMockLayer.sentMessages[0].data[0:3],
                         [0x04, 0x53, 0x61])
        self.assertEqual(len(LinkMockLayer.sentMessages[0].data), 46)

    def testIdentifyEventsAddressed(self):
        # addressed to node
        msg2 = Message(MTI.Identify_Events_Addressed, NodeID(13), NodeID(21))
        self.processor.process(msg2, self.node21)

        self.assertEqual(len(LinkMockLayer.sentMessages), 0)

    def testUnsupportedMessageGlobal(self):
        # global, testing with an MTI we don't understand
        msg1 = Message(MTI.Identify_Producer, NodeID(13), None)
        self.processor.process(msg1, self.node21)

        self.assertEqual(len(LinkMockLayer.sentMessages), 0)

    def testUnsupportedMessageAddressed(self):
        # addressed to node, testing with an MTI we don't understand
        msg2 = Message(MTI.Remote_Button_Request, NodeID(13), NodeID(21))
        self.processor.process(msg2, self.node21)

        self.assertEqual(len(LinkMockLayer.sentMessages), 1)
        self.assertEqual(LinkMockLayer.sentMessages[0].mti,
                         MTI.Optional_Interaction_Rejected)
        self.assertEqual(len(LinkMockLayer.sentMessages[0].data), 4)
        self.assertEqual(LinkMockLayer.sentMessages[0].data,
                         [0x10, 0x43, 0x09, 0x48])  # error code, MTI

    def testDontRejectOIR(self):
        msg1 = Message(MTI.Optional_Interaction_Rejected, NodeID(13),
                       NodeID(21))
        self.processor.process(msg1, self.node21)

        self.assertEqual(len(LinkMockLayer.sentMessages), 0)

    def testDontRejectTDE(self):
        msg1 = Message(MTI.Terminate_Due_To_Error, NodeID(13), NodeID(21))
        self.processor.process(msg1, self.node21)

        self.assertEqual(len(LinkMockLayer.sentMessages), 0)


if __name__ == '__main__':
    unittest.main()
