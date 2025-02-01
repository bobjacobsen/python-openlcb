import unittest

from openlcb.nodestore import NodeStore

from openlcb.node import Node
from openlcb.nodeid import NodeID


class TestNodeStoreClass(unittest.TestCase):

    def testIsPresent(self) :
        dut = NodeStore()

        node = Node(NodeID(120))
        dut.store(node)

        self.assertEqual(dut.isPresent(NodeID(120)), True, "is present")

        self.assertEqual(dut.isPresent(NodeID(123)), False, "is present")

    def testAsArray(self) :
        dut = NodeStore()

        node1 = Node(NodeID(120))
        dut.store(node1)

        node2 = Node(NodeID(240))
        dut.store(node2)

        self.assertEqual(dut.asArray(), [node1, node2],
                         "as array")


if __name__ == '__main__':
    unittest.main()
