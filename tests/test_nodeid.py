import unittest

from nodeid import NodeID

class TestNodeIDClass(unittest.TestCase) :

    def testInitString(self) :
        nid = NodeID("0A.0B.0C.0D.0E.0F")
        self.assertEqual(str(nid), "0A.0B.0C.0D.0E.0F")

    def testDescription(self) :
        nid = NodeID(0x0A_0B_0C_0D_0E_0F)
        self.assertEqual(str(nid), "0A.0B.0C.0D.0E.0F")
 
        nid2 = NodeID(0xFA_FB_FC_FD_FE_FF)
        self.assertEqual(str(nid2), "FA.FB.FC.FD.FE.FF")
    
    def testEquality(self) :
        nid12 = NodeID(12)
        nid12a = NodeID(12)
        nid13 = NodeID(13)
        self.assertEqual(nid12, nid12a, "same contents equal")
        self.assertNotEqual(nid12, nid13, "different contents not equal")
        
        nidDef1 = NodeID(0x05_01_01_01_03_01)
        nidDef2 = NodeID(0x05_01_01_01_03_01)
        self.assertEqual(nidDef1, nidDef2, "default contents equal")
    
    def testToArray(self) :
        arr = NodeID(0x05_01_01_01_03_01).toArray()
        self.assertEqual(arr, [5, 1, 1, 1, 3, 1])
        self.assertEqual(NodeID(arr), NodeID(0x05_01_01_01_03_01), "array operations")

if __name__ == '__main__':
    unittest.main()
