import unittest

from openlcb.node import Node
from openlcb.nodeid import NodeID
from openlcb.remotenodestore import RemoteNodeStore


class TestRemoteNodeStoreClass(unittest.TestCase) :

    def testSimpleLoadStore(self) :
        store = RemoteNodeStore(NodeID(1))

        n12 = Node(NodeID(12))

        store.store(n12)
        store.store(Node(NodeID(13)))

        self.assertEqual(store.lookup(NodeID(12)), n12, "store then lookup OK")

    def testRequestCreates(self) :
        nodeStore = RemoteNodeStore(NodeID(1))

        # try a load
        temp = nodeStore.lookup(NodeID(12))

        self.assertEqual(temp, None, "lookup returns None if node not present")

    def testAccessThroughLoadStoreByID(self) :
        nodeStore = RemoteNodeStore(NodeID(1))

        nid12 = NodeID(12)
        nid13 = NodeID(13)

        n12 = Node(nid12)
        n13 = Node(nid13)

        nodeStore.store(n12)
        nodeStore.store(n13)

        # test ability to modify state
        n12.state = Node.State.Initialized
        self.assertEqual(n12.state, Node.State.Initialized,
                         "local modification OK")
        self.assertEqual(nodeStore.lookup(nid12).state, Node.State.Initialized,
                         "original in store modified")

        # lookup non-existing node returns None
        self.assertEqual(nodeStore.lookup(NodeID(21)), None,
                         "None on no match in store")

        temp = nodeStore.lookup(nid13)
        temp.state = Node.State.Uninitialized
        nodeStore.store(temp)
        self.assertEqual(nodeStore.lookup(nid13).state,
                         Node.State.Uninitialized,
                         "original in store modified by replacement")

    def testALocalStoreVeto(self) :
        nid12 = NodeID(12)
        n12 = Node(nid12)

        nid13 = NodeID(13)

        store = RemoteNodeStore(nid13)

        store.store(n12)

        # lookup non-existing node doesn't create it if in local store
        self.assertEqual(store.lookup(nid13), None,
                         "don't create if in local store")

    def testCustomStringConvertible(self) :
        # existence test, don't check content which can change
        store = RemoteNodeStore(NodeID(13))
        store.description


if __name__ == '__main__':
    unittest.main()
