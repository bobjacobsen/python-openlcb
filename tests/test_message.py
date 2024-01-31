import unittest

from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.nodeid import NodeID


class TestMessageClass(unittest.TestCase):

    def testDescription3Args(self):
        message = Message(MTI.Identify_Consumer, NodeID(12), NodeID(13), [])
        self.assertEqual(str(message), "Message (Identify_Consumer)")

    def testDescription2Args(self):
        message = Message(MTI.Identify_Consumer, NodeID(12), None, [])
        self.assertEqual(str(message), "Message (Identify_Consumer)")

    def testGlobalAddressed(self):
        self.assertTrue(Message(MTI.Initialization_Complete, NodeID(0),
                                None, []).isGlobal())
        self.assertFalse(Message(MTI.Initialization_Complete, NodeID(0),
                                 None, []).isAddressed())

        self.assertTrue(Message(MTI.Verify_NodeID_Number_Addressed, NodeID(0),
                                None, []).isAddressed())
        self.assertFalse(Message(MTI.Verify_NodeID_Number_Addressed, NodeID(0),
                                 None, []).isGlobal())


if __name__ == '__main__':
    unittest.main()
