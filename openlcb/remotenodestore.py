'''
Store for seen remote (not implemented here) nodes
'''

from openlcb.nodestore import NodeStore

from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.node import Node
from openlcb.nodeid import NodeID


class RemoteNodeStore(NodeStore) :
    '''Accumulates Nodes that it sees requested
    unless they're already in a given local NodeStore.
    '''

    def __init__(self, localNodeID) :
        self.localNodeID = localNodeID
        NodeStore.__init__(self)

    def description(self) :
        '''Provide a more detailed string description
        '''
        return "RemoteNodeStore w {}".format(self.nodes.count)

    def checkForNewNode(self, message) :
        '''Check if the message is to a new node.
        Returns:
            bool: True if the message is to a new node, so that
                createNewRemoteNode should be called.
        '''
        node_id = message.source
        if node_id == self.localNodeID :
            # present in other store, skip
            return False
        # NodeID(0) is a special case, used for
        #   e.g. linkUp, linkDown; don't store
        if node_id == NodeID(0) :
            return False
        # make sure source node is in store if it needs to be
        if self.lookup(message.source) is not None :
            return False
        return True

    def createNewRemoteNode(self, message) :
        '''
        A new node was found by checkForNewNode, so this
        mutates the store to add this.  This should only be called
        if checkForNewNode is true to avoid excess publishing!
        - Parameter message: Incoming message to process
        '''
        # need to create the node and process it's New_Node_Seen
        nodeID = message.source
        node = Node(nodeID)

        self.store(node)
        # All nodes process a notification that there's a new node
        new_message = Message(MTI.New_Node_Seen, nodeID, None)
        for processor in self.processors :
            processor.process(new_message, node)

    def processMessageFromLinkLayer(self, message) :
        '''Process an incoming message
        across all the nodes in the remote node store.

        Args:
            message (Message): Incoming message to process

        Returns:
            bool: True is any of the nodes indicated a significant change.
        '''
        publish = False

        if self.checkForNewNode(message) :
            self.createNewRemoteNode(message)
            publish = True
        # always run invoke Processsors on nodes
        publish = self.invokeProcessorsOnNodes(message) or publish
        return publish
