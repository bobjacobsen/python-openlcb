import unittest

from canframe import CanFrame
from nodeid import NodeID

class TestCanFrameClass(unittest.TestCase) :

    def testInit(self) :
        frame1 = CanFrame(0, [])
        self.assertEqual(frame1.header, 0x0_000_000)
        self.assertEqual(frame1.data, [])

        frame2 = CanFrame(0x1234, [])
        self.assertEqual(frame2.header, 0x1234)
        self.assertEqual(frame2.data, [])

        frame3 = CanFrame(0x123456, [1,2,3])
        self.assertEqual(frame3.header, 0x123456)
        self.assertEqual(frame3.data, [1,2,3])
    
    def testCID(self) :
        cidFrame40 = CanFrame(4, NodeID(0x00_00_00_00_00_00), 0)
        self.assertEqual(cidFrame40.header, 0x14_000_000)
        self.assertEqual(cidFrame40.data, [])

        cidFrame4ABC = CanFrame(4, NodeID(0x00_00_00_00_00_00), 0xABC)
        self.assertEqual(cidFrame4ABC.header, 0x14_000_ABC)
        self.assertEqual(cidFrame4ABC.data, [])

        cidFrame4 = CanFrame(4, NodeID(0x12_34_56_78_9A_BC), 0x123)
        self.assertEqual(cidFrame4.header, 0x14_ABC_123)
        self.assertEqual(cidFrame4.data, [])

        cidFrame5 = CanFrame(5, NodeID(0x12_34_56_78_9A_BC), 0x321)
        self.assertEqual(cidFrame5.header, 0x15_789_321)
        self.assertEqual(cidFrame5.data, [])

        cidFrame7 = CanFrame(7, NodeID(0x12_34_56_78_9A_BC), 0x010)
        self.assertEqual(cidFrame7.header, 0x17_123_010)
        self.assertEqual(cidFrame7.data, [])

    def testControlFrame(self) :
        frame0703 = CanFrame(0x0701, 0x123)
        self.assertEqual(frame0703.header, 0x10701123)
        self.assertEqual(frame0703.data, [])
        
if __name__ == '__main__':
    unittest.main()
