# -*- coding: utf-8 -*-
import os
import sys
import unittest

if __name__ == "__main__":
    # Allow importing repo copy of openlcb if running tests from repo manually.
    TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
    REPO_DIR = os.path.dirname(TESTS_DIR)
    sys.path.insert(0, REPO_DIR)

from openlcb.nodeid import NodeID
from openlcb.linklayer import LinkLayer
from openlcb.mti import MTI
from openlcb.message import Message
from openlcb.memoryservice import (
    MemoryReadMemo,
    MemoryWriteMemo,
    MemoryService,
)
from openlcb.datagramservice import (
    # DatagramWriteMemo,
    # DatagramReadMemo,
    DatagramService,
)


class LinkMockLayer(LinkLayer):
    sentMessages = []

    def sendMessage(self, message):
        LinkMockLayer.sentMessages.append(message)


class TestMemoryServiceClass(unittest.TestCase):

    def callbackR(self, memo):
        self.returnedMemoryReadMemo.append(memo)

    def callbackW(self, memo):
        self.returnedMemoryWriteMemo.append(memo)

    def setUp(self):
        LinkMockLayer.sentMessages = []
        self.returnedMemoryReadMemo = []
        self.returnedMemoryWriteMemo = []
        self.dService = DatagramService(LinkMockLayer(NodeID(12)))
        self.mService = MemoryService(self.dService)

    def testReturnCyrillicStrings(self):
        # See also testReturnCyrillicStrings in test_snip
        # If you have characters specific to UTF-8 (either in code or comment)
        #   add the following as the 1st or 2nd line of the py file:
        # -*- coding: utf-8 -*-
        data = [0xd0, 0x94, 0xd0, 0xbc, 0xd0, 0xb8, 0xd1, 0x82, 0xd1, 0x80, 0xd0, 0xb8, 0xd0, 0xb9]   # Cyrillic spelling of the name Dmitry (7 characters becomes 14 bytes)
        self.assertEqual(self.mService.arrayToString(data, len(data)), "Дмитрий")  # Cyrillic spelling of the name Dmitry. This string should appear as 7 Cyrillic characters like Dmitry-Cyrillic.png in doc (14 bytes in a hex editor), otherwise your editor does not support utf-8 and editing this file with it could break it.

    def testSingleRead(self):
        memMemo = MemoryReadMemo(NodeID(123), 64, 0xFD, 0,
                                 self.callbackR, self.callbackR)
        self.mService.requestMemoryRead(memMemo)
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)
        # ^ memory request datagram sent

        # have to reply through DatagramService
        self.dService.process(Message(MTI.Datagram_Received_OK, NodeID(123),
                                      NodeID(12)))
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)
        # ^ memory request datagram sent
        self.assertEqual(LinkMockLayer.sentMessages[0].data,
                         [0x20, 0x41, 0, 0, 0, 0, 64])
        self.assertEqual(len(self.returnedMemoryReadMemo), 0)
        # ^ no memory read op returned

        self.dService.process(Message(MTI.Datagram, NodeID(123), NodeID(12),
                                      [0x20, 0x51, 0, 0, 0, 0, 1, 2, 3, 4]))
        self.assertEqual(len(LinkMockLayer.sentMessages), 2)
        # read reply datagram reply sent
        self.assertEqual(len(self.returnedMemoryReadMemo), 1)
        # memory read returned

    def testSingleWrite(self):
        memMemo = MemoryWriteMemo(NodeID(123),
                                  self.callbackW, self.callbackW,
                                  64, 0xFD, 0,
                                  [1, 2, 3])
        self.mService.requestMemoryWrite(memMemo)
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)
        # ^ memory request datagram sent

        # have to reply through DatagramService
        self.dService.process(Message(MTI.Datagram_Received_OK, NodeID(123),
                                      NodeID(12)))
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)
        # ^ memory request datagram sent
        self.assertEqual(LinkMockLayer.sentMessages[0].data,
                         [0x20, 0x01,
                          0, 0, 0, 0,
                          1, 2, 3])
        self.assertEqual(len(self.returnedMemoryWriteMemo), 0)
        # ^ no memory write op returned

        self.dService.process(Message(MTI.Datagram, NodeID(123), NodeID(12),
                                      [0x20,
                                       0x11,
                                       0, 0, 0, 0]))
        self.assertEqual(len(LinkMockLayer.sentMessages), 2)
        # ^ write reply datagram reply sent
        self.assertEqual(len(self.returnedMemoryWriteMemo), 1)
        # ^ memory write returned

    def testMultipleRead(self):

        # make three requests, only one of which should go forward at a time
        memMemo0 = MemoryReadMemo(NodeID(123), 64, 0xFD, 0,
                                  self.callbackR, self.callbackR)
        self.mService.requestMemoryRead(memMemo0)
        memMemo64 = MemoryReadMemo(NodeID(123), 32, 0xFD, 64,
                                   self.callbackR, self.callbackR)
        self.mService.requestMemoryRead(memMemo64)
        memMemo128 = MemoryReadMemo(NodeID(123), 16, 0xFD, 128,
                                    self.callbackR, self.callbackR)
        self.mService.requestMemoryRead(memMemo128)

        self.assertEqual(len(LinkMockLayer.sentMessages), 1)
        # ^ only one memory request datagram sent

        # have to reply through DatagramService
        self.dService.process(Message(MTI.Datagram_Received_OK, NodeID(123),
                                      NodeID(12)))
        self.assertEqual(len(LinkMockLayer.sentMessages), 1)  # memory request datagram sent  # noqa: E501
        self.assertEqual(LinkMockLayer.sentMessages[0].data, [0x20, 0x41, 0,0,0,0, 64])  # noqa: E231,E501
        self.assertEqual(len(self.returnedMemoryReadMemo), 0)  # no memory read op returned  # noqa: E501

        self.dService.process(Message(MTI.Datagram, NodeID(123), NodeID(12), [0x20, 0x51, 0,0,0,0, 1,2,3,4]))  # noqa: E231,E501
        self.assertEqual(len(LinkMockLayer.sentMessages), 3)  # read reply datagram reply sent and next datagram sent  # noqa: E501
        self.assertEqual(len(self.returnedMemoryReadMemo), 1)  # memory read returned  # noqa: E501

        # walk through 2nd datagram
        self.dService.process(Message(MTI.Datagram_Received_OK, NodeID(123),
                                      NodeID(12)))
        self.assertEqual(len(LinkMockLayer.sentMessages), 3)  # memory request datagram sent  # noqa: E501
        self.assertEqual(LinkMockLayer.sentMessages[2].data, [0x20, 0x41, 0,0,0,64, 32])  # noqa: E231,E501
        self.assertEqual(len(self.returnedMemoryReadMemo), 1)  # no memory read op returned  # noqa: E501

        self.dService.process(Message(MTI.Datagram, NodeID(123), NodeID(12),
                                      [0x20, 0x51,
                                       0, 0, 0, 64,
                                       1, 2, 3, 4]))
        self.assertEqual(len(LinkMockLayer.sentMessages), 5)  # read reply datagram reply sent and next datagram sent  # noqa: E501
        self.assertEqual(len(self.returnedMemoryReadMemo), 2)  # memory read returned  # noqa: E501

    def testArrayToString(self):
        sut = self.mService.arrayToString([0x41, 0x42, 0x43, 0x44], 4)
        self.assertEqual(sut, "ABCD")

        sut = self.mService.arrayToString([0x41, 0x42, 0, 0x44], 4)
        self.assertEqual(sut, "AB")

        sut = self.mService.arrayToString([0x41, 0x42, 0x43, 0x44], 2)
        self.assertEqual(sut, "AB")

        sut = self.mService.arrayToString([0x41, 0x42, 0x43, 0], 4)
        self.assertEqual(sut, "ABC")

        sut = self.mService.arrayToString([0x41, 0x42, 0x31, 0x32], 8)
        self.assertEqual(sut, "AB12")

    def testStringToArray(self):
        aut = self.mService.stringToArray("ABCD", 4)
        self.assertEqual(aut, [0x41, 0x42, 0x43, 0x44])

        aut = self.mService.stringToArray("ABCD", 2)
        self.assertEqual(aut, [0x41, 0x42])

        aut = self.mService.stringToArray("ABCD", 6)
        self.assertEqual(aut, [0x41, 0x42, 0x43, 0x44, 0x00, 0x00])

    def testSpaceDecode(self):
        byte6 = False
        space = 0x00

        (byte6, space) = self.mService.spaceDecode(0xF8)
        self.assertEqual(space, 0xF8)
        self.assertTrue(byte6)

        (byte6, space) = self.mService.spaceDecode(0xFF)
        self.assertEqual(space, 0x03)
        self.assertFalse(byte6)

        (byte6, space) = self.mService.spaceDecode(0xFD)
        self.assertEqual(space, 0x01)
        self.assertFalse(byte6)


if __name__ == '__main__':
    unittest.main()
