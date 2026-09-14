import unittest

from openlcb.datagramservice import (
    DatagramReceiveMemo,
    DatagramSendMemo,
    DatagramService,
)
from openlcb.linklayer import LinkLayer
from openlcb.mti import MTI
from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.physicallayer import PhysicalLayer


class MockPhysicalLayer(PhysicalLayer):
    pass


class LinkMockLayer(LinkLayer):
    sentMessages = []

    class State:
        Initial = 0
        Disconnected = 1
        Permitted = 2

    DisconnectedState = State.Disconnected

    def sendMessage(self, msg, verbose=False):
        LinkMockLayer.sentMessages.append(msg)

    def _onStateChanged(self, oldState, newState):
        print(f"[TcpLink] _onStateChanged from {oldState} to {newState}"
              " (nothing to clean up since LinkMockLayer)")


class DatagramServiceTest(unittest.TestCase):
    def setUp(self):
        self.service = DatagramService(
            LinkMockLayer(MockPhysicalLayer(), NodeID(12))
        )
        LinkMockLayer.sentMessages = []
        self.received = False
        self.receiveMemos = []  # type: list[DatagramReceiveMemo]
        self.callback = False

    def receiveListener(self, msg):
        self.received = True
        self.receiveMemos.append(msg)
        return True

    def testFireDatagramReceived(self):
        msg = DatagramReceiveMemo(NodeID(12), bytearray())
        receiver = self.receiveListener

        self.service.registerDatagramReceivedListener(receiver)

        self.service.fireDatagramReceived(msg)

        self.assertTrue(self.received)

    def testWriteMemoEquatable(self):
        dm1a = DatagramSendMemo(NodeID(2), bytearray())
        dm1b = DatagramSendMemo(NodeID(2), bytearray())
        dm2 = DatagramSendMemo(NodeID(12), bytearray())
        dm3 = DatagramSendMemo(NodeID(12), bytearray([1]))
        dm4 = DatagramSendMemo(NodeID(12), bytearray([1, 2, 3]))

        self.assertEqual(dm1a, dm1b)
        self.assertNotEqual(dm1a, dm2)
        self.assertEqual(dm2, dm2)
        self.assertNotEqual(dm2, dm3)
        self.assertNotEqual(dm2, dm4)
        self.assertNotEqual(dm3, dm4)

    def testReadMemoEquatable(self):
        dm1a = DatagramReceiveMemo(NodeID(1), bytearray())
        dm1b = DatagramReceiveMemo(NodeID(1), bytearray())
        dm2 = DatagramReceiveMemo(NodeID(11), bytearray())
        dm3 = DatagramReceiveMemo(NodeID(11), bytearray([1]))
        dm4 = DatagramReceiveMemo(NodeID(11), bytearray([1, 2, 3]))

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

    def sendCallBackCheck(self, memo):
        self.callback = True

    def testSendDatagramOK(self):
        sendMemo = DatagramSendMemo(NodeID(22),
                                    bytearray([0x20, 0x42, 0x30]),
                                    self.sendCallBackCheck)

        self.service.sendDatagram(sendMemo)

        self.assertEqual(len(LinkMockLayer.sentMessages), 1)

        # send a reply back through
        message = Message(MTI.Datagram_Received_OK, NodeID(22), NodeID(12))
        self.service.process(message)
        # was callback called?
        self.assertTrue(self.callback)

    def testSendThreeDatagramOK(self):
        sendMemo = DatagramSendMemo(NodeID(22),
                                    bytearray([0x20, 0x42, 0x30]),
                                    self.sendCallBackCheck)

        self.service.sendDatagram(sendMemo)
        self.service.sendDatagram(sendMemo)
        self.service.sendDatagram(sendMemo)

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
        sendMemo = DatagramSendMemo(NodeID(22),
                                    bytearray([0x20, 0x42, 0x30]), None,
                                    self.sendCallBackCheck)

        self.service.sendDatagram(sendMemo)

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
        self.assertEqual(len(self.receiveMemos), 1)

        self.service.positiveReplyToDatagram(self.receiveMemos[0], 0)

        # check message came through
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)

    def testEnum(self):
        usedValues = set()
        # ensure values are unique:
        for entry in DatagramService.ProtocolID:
            self.assertNotIn(entry.value, usedValues)
            usedValues.add(entry.value)
            # print('{} = {}'.format(entry.name, entry.value))


if __name__ == '__main__':
    unittest.main()
