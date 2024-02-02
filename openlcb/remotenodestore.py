from openlcb.nodestore import NodeStore

from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.node import Node
from openlcb.nodeid import NodeID

class RemoteNodeStore(NodeStore) :
    '''
       Accumulates Nodes that it sees requested, unless they're already in a given local NodeStore
    ''' 
    
    def __init__(self, localNodeID) :
        self.localNodeID = localNodeID
        NodeStore.__init__(self)

    def description(self) : return  "RemoteNodeStore w {}".format(nodes.count)

    # return True if the message is to a new node, so that createNewRemoteNode should be called.
    def checkForNewNode(self, message) :
        nodeID = message.source
        if nodeID == self.localNodeID :
            # present in other store, skip
            return False
        # NodeID(0) is a special case, used for e.g. linkUp, linkDown; don't store
        if (nodeID == NodeID(0)) :
            return False
        # make sure source node is in store if it needs to be
        if self.lookup(message.source) is not None :
            return False
        return True
    
    # a new node was found by checkForNewNode, so this
    # mutates the store to add this.  This should only be called
    # if checkForNewNode is true to avoid excess publishing!
    def createNewRemoteNode(self, message) :
        # need to create the node and process it's New_Node_Seen
        nodeID = message.source
        node = Node(nodeID)
        
        self.store(node)
        # All nodes process a notification that there's a new node
        newNodeMessage = Message(MTI.New_Node_Seen, nodeID, None)
        for processor in self.processors :
            processor.process(newNodeMessage, node)

    # Process an incoming message across all the nodes in the remote node store.
    # Returns True is any of the nodes indicated a significant change.
    # - Parameter message: Incoming message to process
    def processMessageFromLinkLayer(self, message) :
        publish = False
        
        if self.checkForNewNode(message) :
            self.createNewRemoteNode(message)
            publish = True
        publish = self.invokeProcessorsOnNodes(message) or publish # always run invoke Processsors on nodes
        return publish
