from openlcb.nodestore import NodeStore

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
        if nodeID == localNodeID :
            # present in other store, skip
            return False
        # NodeID(0) is a special case, used for e.g. linkUp, linkDown; don't store
        if (nodeID == NodeID(0)) :
            return False
        # make sure source node is in store if it needs to be
        if lookup(message.source) is not None :
            return False
        return True
    
    # a new node was found by checkForNewNode, so this
    # mutates the store to add this.  This should only be called
    # if checkForNewNode is true to avoid excess publishing!
    def createNewRemoteNode(self, message) :
        # need to create the node and process it's New_Node_Seen
        nodeID = message.source
        node = Node(nodeID)
        
        store(node)
        # All nodes process a notification that there's a new node
        newNodeMessage = Message(MTI.New_Node_Seen, nodeID, None)
        for processor in processors :
            processor.process(newNodeMessage, node)

