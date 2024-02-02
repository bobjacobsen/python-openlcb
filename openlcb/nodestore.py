from openlcb.nodeid import NodeID

class NodeStore :
    '''
    Store the available Nodes and provide multiple means of retrieval.

    Storage and indexing methods are an internal detail.
    You can't remove a node; once we know about it, we know about it.
    '''
    
    def __init__(self) :
        self.byIdMap = {}
        self.nodes = []
        self.processors = []
            
    # Store a new node or replace an existing stored node
    # - Parameter node: new Node content
    def store(self, node) :
        self.byIdMap[node.id] = node
        self.nodes.append(node)

        # sort by SNIP user name (ascending, blanks at front)
        # This can be too early, when node created but no SNIP yet, so also sort before use in View
        self.nodes.sort( key=lambda x: x.snip.userProvidedNodeName, reverse=True)
        
    def isPresent(self, nodeID ) :
        return self.byIdMap.get(nodeID) is not None
    
    def asArray(self) :
        return [self.byIdMap[i] for i in self.byIdMap]
    
    # Retrieve a Node's content from the store
    # - Parameter is either
    #     userProvidedDescription: string to match SNIP content
    #     nodeID: for direct lookup
    # - Returns: None if the there's no match
    def lookup(self, parm) :
        if isinstance(parm, NodeID) : 
            if not parm in self.byIdMap :
                self.byIdMap[parm] = None
            return self.byIdMap[parm]
        # assume parm is string
        for node in self.byIdMap.values() :
            if (node.snip.userProvidedDescription == parm) :
                return node
        return None
    
    # Process a message across all nodes
    def invokeProcessorsOnNodes(self, message) :
        publish = False  # has any processor returned True?
        for processor in self.processors :
            for node in self.byIdMap.values() :
                publish = processor.process(message, node) or publish # always invoke Processsor on node first
        return publish

