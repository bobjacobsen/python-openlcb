import unittest

from openlcb.datagramservice import (
    DatagramReadMemo,
    DatagramWriteMemo,
    DatagramService,
)
from openlcb.linklayer import LinkLayer
from openlcb.mti import MTI
from openlcb.nodeid import NodeID
from openlcb.message import Message


class LinkMockLayer(LinkLayer):
    sentMessages = []

    def sendMessage(self, message):
        LinkMockLayer.sentMessages.append(message)


class DatagramServiceTest(unittest.TestCase):
    def setUp(self):
        self.service = DatagramService(LinkMockLayer(NodeID(12)))
        LinkMockLayer.sentMessages = []
        self.received = False
        self.readMemos = []
        self.callback = False

    def receiveListener(self, msg):
        self.received = True
        self.readMemos.append(msg)
        return True

    def testFireListeners(self):
        msg = DatagramReadMemo(NodeID(12), [])
        receiver = self.receiveListener

        self.service.registerDatagramReceivedListener(receiver)

        self.service.fireListeners(msg)

        self.assertTrue(self.received)

    def testWriteMemoEquatable(self):
        dm1a = DatagramWriteMemo(NodeID(2), [])
        dm1b = DatagramWriteMemo(NodeID(2), [])
        dm2 = DatagramWriteMemo(NodeID(12), [])
        dm3 = DatagramWriteMemo(NodeID(12), [1])
        dm4 = DatagramWriteMemo(NodeID(12), [1, 2, 3])

        self.assertEqual(dm1a, dm1b)
        self.assertNotEqual(dm1a, dm2)
        self.assertEqual(dm2, dm2)
        self.assertNotEqual(dm2, dm3)
        self.assertNotEqual(dm2, dm4)
        self.assertNotEqual(dm3, dm4)

    def testReadMemoEquatable(self):
        dm1a = DatagramReadMemo(NodeID(1), [])
        dm1b = DatagramReadMemo(NodeID(1), [])
        dm2 = DatagramReadMemo(NodeID(11), [])
        dm3 = DatagramReadMemo(NodeID(11), [1])
        dm4 = DatagramReadMemo(NodeID(11), [1, 2, 3])

        self.assertEqual(dm1a, dm1b)
        self.assertNotEqual(dm1a, dm2)
        self.assertEqual(dm2, dm2)
        self.assertNotEqual(dm2, dm3)
        self.assertNotEqual(dm2, dm4)
        self.assertNotEqual(dm3, dm4)

    def testDatagramType(self):
        self.assertEqual(self.service.datagramType([]),
                         DatagramService.ProtocolID.Unrecognized)
        self.assertEqual(self.service.datagramType([0, 2, 3]),
                         DatagramService.ProtocolID.Unrecognized)

        self.assertEqual(self.service.datagramType([0x20, 2, 3]),
                         DatagramService.ProtocolID.MemoryOperation)

    def writeCallBackCheck(self, memo):
        self.callback = True

    def testSendDatagramOK(self):
        writeMemo = DatagramWriteMemo(NodeID(22), [0x20, 0x42, 0x30],
                                      self.writeCallBackCheck)

        self.service.sendDatagram(writeMemo)

        self.assertEqual(len(LinkMockLayer.sentMessages), 1)

        # send a reply back through
        message = Message(MTI.Datagram_Received_OK, NodeID(22), NodeID(12))
        self.service.process(message)
        # was callback called?
        self.assertTrue(self.callback)

    def testSendThreeDatagramOK(self):
        writeMemo = DatagramWriteMemo(NodeID(22), [0x20, 0x42, 0x30],
                                      self.writeCallBackCheck)

        self.service.sendDatagram(writeMemo)
        self.service.sendDatagram(writeMemo)
        self.service.sendDatagram(writeMemo)

        self.assertEqual(len(LinkMockLayer.sentMessages), 1)
        # ^ only first is send until reply

        # send a reply back through
        message = Message(MTI.Datagram_Received_OK, NodeID(22), NodeID(12))
        self.service.process(message)
        # was callback called?
        self.assertTrue(self.callback)
        self.callback = False

        # next should have been sent
        self.assertEqual(len(LinkMockLayer.sentMessages), 2)
        # send a reply back through
        self.service.process(message)
        # was callback called?
        self.assertTrue(self.callback)
        self.callback = False

        # next should have been sent
        self.assertEqual(len(LinkMockLayer.sentMessages), 3)
        # send a reply back through
        self.service.process(message)
        # was callback called?
        self.assertTrue(self.callback)
        self.callback = False

        # that should be it
        self.assertEqual(len(LinkMockLayer.sentMessages), 3)

    def testSendDatagramRejected(self):
        writeMemo = DatagramWriteMemo(NodeID(22), [0x20, 0x42, 0x30], None,
                                      self.writeCallBackCheck)

        self.service.sendDatagram(writeMemo)

        self.assertEqual(len(LinkMockLayer.sentMessages), 1)

        # send a reply back through
        message = Message(MTI.Datagram_Rejected, NodeID(22), NodeID(12))
        self.service.process(message)
        # was callback called?
        self.assertTrue(self.callback)

    def testReceiveDatagramOK(self):
        # set up datagram listener
        receiver = self.receiveListener
        self.service.registerDatagramReceivedListener(receiver)

        # receive a datagram
        message = Message(MTI.Datagram, NodeID(22), NodeID(12))
        self.service.process(message)

        # check that it went through
        self.assertTrue(self.received)
        self.assertEqual(len(self.readMemos), 1)

        self.service.positiveReplyToDatagram(self.readMemos[0], 0)

        # check message came through
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)


if __name__ == '__main__':
    unittest.main()
