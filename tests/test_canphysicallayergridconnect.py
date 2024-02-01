import unittest

from canbus.canphysicallayergridconnect import CanPhysicalLayerGridConnect
from canbus.canframe import CanFrame
from openlcb.nodeid import NodeID


class CanPhysicalLayerGridConnectTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(CanPhysicalLayerGridConnectTest, self).__init__(*args, **kwargs)
        self.capturedString = ""
        self.receivedFrames = []

    # PHY side
    def captureString(self, string):
        self.capturedString = string

    # Link Layer side
    def receiveListener(self, frame):
        self.receivedFrames += [frame]

    def testCID4Sent(self):
        gc = CanPhysicalLayerGridConnect(self.captureString)

        gc.sendCanFrame(CanFrame(4, NodeID(0x010203040506), 0xABC))
        self.assertEqual(self.capturedString, ":X14506ABCN;\n")

    def testVerifyNodeSent(self):
        gc = CanPhysicalLayerGridConnect(self.captureString)

        gc.sendCanFrame(CanFrame(0x19170, 0x365, [0x02, 0x01, 0x12, 0xFE,
                                                  0x05, 0x6C]))
        self.assertEqual(self.capturedString, ":X19170365N020112FE056C;\n")

    def testOneFrameReceivedExactlyHeaderOnly(self):
        gc = CanPhysicalLayerGridConnect(self.captureString)
        gc.registerFrameReceivedListener(self.receiveListener)
        bytes = [0x3a, 0x58, 0x31, 0x39, 0x34, 0x39, 0x30, 0x33, 0x36, 0x35,
                 0x4e, 0x3b, 0x0a]  # :X19490365N;

        gc.receiveChars(bytes)

        self.assertEqual(self.receivedFrames[0], CanFrame(0x19490365, []))

    def testOneFrameReceivedExactlyWithData(self):
        gc = CanPhysicalLayerGridConnect(self.captureString)
        gc.registerFrameReceivedListener(self.receiveListener)
        bytes = [0x3a, 0x58, 0x31, 0x39, 0x31, 0x42, 0x30, 0x33, 0x36, 0x35,
                 0x4e, 0x30,
                 0x32, 0x30, 0x31, 0x31, 0x32, 0x46, 0x45, 0x30, 0x35, 0x36,
                 0x43, 0x3b]
        # :X19170365N020112FE056C;

        gc.receiveChars(bytes)

        self.assertEqual(
            self.receivedFrames[0],
            CanFrame(0x191B0365, [0x02, 0x01, 0x12, 0xFE, 0x05, 0x6C])
        )

    def testOneFrameReceivedHeaderOnlyTwice(self):
        gc = CanPhysicalLayerGridConnect(self.captureString)
        gc.registerFrameReceivedListener(self.receiveListener)
        bytes = [0x3a, 0x58, 0x31, 0x39, 0x34, 0x39, 0x30, 0x33, 0x36, 0x35,
                 0x4e, 0x3b, 0x0a]  # :X19490365N;

        gc.receiveChars(bytes+bytes)

        self.assertEqual(self.receivedFrames[0], CanFrame(0x19490365, []))
        self.assertEqual(self.receivedFrames[1], CanFrame(0x19490365, []))

    def testOneFrameReceivedHeaderOnlyPlusPartOfAnother(self):
        gc = CanPhysicalLayerGridConnect(self.captureString)
        gc.registerFrameReceivedListener(self.receiveListener)
        bytes = [0x3a, 0x58, 0x31, 0x39, 0x34, 0x39, 0x30, 0x33, 0x36,
                 0x35, 0x4e, 0x3b, 0x0a,  # :X19490365N;
                 0x3a, 0x58]
        gc.receiveChars(bytes)

        self.assertEqual(self.receivedFrames[0], CanFrame(0x19490365, []))

        bytes = [0x31, 0x39, 0x34, 0x39, 0x30, 0x33,
                 0x36, 0x35, 0x4e, 0x3b, 0x0a]
        gc.receiveChars(bytes)

        self.assertEqual(self.receivedFrames[1], CanFrame(0x19490365, []))

    def testOneFrameReceivedInTwoChunks(self):
        gc = CanPhysicalLayerGridConnect(self.captureString)
        gc.registerFrameReceivedListener(self.receiveListener)
        bytes1 = [0x3a, 0x58, 0x31, 0x39, 0x31, 0x37, 0x30, 0x33, 0x36, 0x35,
                  0x4e, 0x30]
        # :X19170365N020112FE056C;

        gc.receiveChars(bytes1)

        bytes2 = [0x32, 0x30, 0x31, 0x31, 0x32, 0x46, 0x45, 0x30, 0x35, 0x36,
                  0x43, 0x3b]
        gc.receiveChars(bytes2)

        self.assertEqual(
            self.receivedFrames[0],
            CanFrame(0x19170365, [0x02, 0x01, 0x12, 0xFE, 0x05, 0x6C])
        )

    def testSequence(self):
        gc = CanPhysicalLayerGridConnect(self.captureString)
        gc.registerFrameReceivedListener(self.receiveListener)
        bytes = [0x3a, 0x58, 0x31, 0x39, 0x34, 0x39, 0x30, 0x33,
                 0x36, 0x35, 0x4e, 0x3b, 0x0a]
        # :X19490365N;

        gc.receiveChars(bytes)

        self.assertEqual(len(self.receivedFrames), 1)
        self.assertEqual(self.receivedFrames[0], CanFrame(0x19490365, []))
        self.receivedFrames = []

        gc.receiveChars(bytes)
        self.assertEqual(len(self.receivedFrames), 1)
        self.assertEqual(self.receivedFrames[0], CanFrame(0x19490365, []))


if __name__ == '__main__':
    unittest.main()

