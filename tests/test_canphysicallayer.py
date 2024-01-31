import unittest

from canbus.canphysicallayer import CanPhysicalLayer
from canbus.canframe import CanFrame


class TestCanPhysicalLayerClass(unittest.TestCase):

    # test function marks that the listeners were fired
    received = False

    def receiveListener(self, frame):
        self.received = True

    def testReceipt(self):
        self.received = False
        frame = CanFrame(0x000, [])
        receiver = self.receiveListener
        layer = CanPhysicalLayer()
        layer.registerFrameReceivedListener(receiver)

        layer.fireListeners(frame)

        self.assertTrue(self.received)


if __name__ == '__main__':
    unittest.main()
