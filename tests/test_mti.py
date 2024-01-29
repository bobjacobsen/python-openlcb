import unittest

from mti import MTI

class TestMTIClass(unittest.TestCase) :

    def testInitFromInt(self) :
        self.assertEqual(MTI(0x08F4), MTI.Identify_Consumer)

    def testPriority(self) :
        self.assertEqual(MTI(0x08F4).priority(),2)

    def testAddressPresent(self) :
        self.assertFalse(MTI(0x08F4).addressPresent())
        self.assertTrue(MTI(0x0828).addressPresent())

    def testEventIDPresent(self) :
        self.assertTrue(MTI(0x08F4).eventIDPresent())
        self.assertFalse(MTI(0x0828).eventIDPresent())

    def testSimpleProtocol(self) :
        self.assertTrue(MTI(0x08F4).simpleProtocol())
        self.assertFalse(MTI(0x0828).simpleProtocol())

    def testIsGlobal(self) :
        self.assertTrue(MTI(0x08F4).isGlobal())
        self.assertFalse(MTI(0x0828).isGlobal())
        self.assertTrue(MTI.Initialization_Complete.isGlobal())
        self.assertFalse(MTI.Protocol_Support_Inquiry.isGlobal())
        
        self.assertTrue(MTI.Link_Layer_Up.isGlobal())     # needs to be global so all node implementations see it
        self.assertTrue(MTI.Link_Layer_Down.isGlobal())   # needs to be global so all node implementations see it


if __name__ == '__main__':
    unittest.main()
