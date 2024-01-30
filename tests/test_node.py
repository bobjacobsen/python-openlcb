import unittest

from openlcb.node import Node
from openlcb.nodeid import NodeID
from openlcb.pip import PIP
from openlcb.snip import SNIP


class TestNodeClass(unittest.TestCase):

    def testContents(self):
        nid12 = NodeID(12)

        n12 = Node(nid12)

        n12.state = Node.State.Initialized
        self.assertEqual(n12.state, Node.State.Initialized)

    def testDescription(self):
        nid = NodeID(0x0A0B0C0D0E0F)
        self.assertEqual(str(Node(nid)), "Node (0A.0B.0C.0D.0E.0F)")

    def testName(self):
        nid = NodeID(0x0A0B0C0D0E0F)
        node = Node(nid)
        node.snip.userProvidedNodeName = "test 123"
        self.assertEqual(node.name(), "test 123")

    def testEquatable(self):
        nid12 = NodeID(12)
        n12 = Node(nid12)
        n12.state = Node.State.Initialized  # should not affect equality

        nid12a = NodeID(12)
        n12a = Node(nid12a)

        nid13 = NodeID(13)
        n13 = Node(nid13)

        self.assertEqual(n12, n12a)
        self.assertNotEqual(n12, n13)

    def testComparable(self):
        nid12 = NodeID(12)
        n12 = Node(nid12)
        n12.state = Node.State.Initialized  # should not affect comparison

        nid13 = NodeID(13)
        n13 = Node(nid13)

        self.assertFalse(n12 < n12)
        self.assertFalse(n12 > n12)

        self.assertFalse(n13 < n12)
        self.assertTrue(n12 < n13)

    def testHash(self):
        nid12 = NodeID(12)
        n12 = Node(nid12)
        n12.state = Node.State.Initialized  # should not affect equality

        nid12a = NodeID(12)
        n12a = Node(nid12a)

        nid13 = NodeID(13)
        n13 = Node(nid13)

        testSet = set([n12, n12a, n13])
        self.assertEqual(testSet, set([n12, n13]))

    def testPipSet(self):
        n12 = Node(NodeID(12))

        self.assertEqual(n12.pipSet, set([]))

        n12.pipSet = set([PIP.DISPLAY_PROTOCOL])

        self.assertEqual(n12.pipSet, set([PIP.DISPLAY_PROTOCOL]))

        self.assertTrue(PIP.DISPLAY_PROTOCOL in n12.pipSet)
        self.assertFalse(PIP.STREAM_PROTOCOL in n12.pipSet)

    def testConvenienceCtors(self):
        pipSet = set([PIP.DISPLAY_PROTOCOL])
        n1 = Node(NodeID(12), pipSet=pipSet)
        self.assertTrue(PIP.DISPLAY_PROTOCOL in n1.pipSet)

        snip = SNIP()
        snip.modelName = "modelX"
        n2 = Node(NodeID(13), snip)
        self.assertTrue(n2.snip.modelName == "modelX")


if __name__ == '__main__':
    unittest.main()
