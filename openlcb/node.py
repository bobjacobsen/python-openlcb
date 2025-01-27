'''
based on Node.swift

Created by Bob Jacobsen on 6/1/22.

Central organizing point for information contained in a physical Node.

This is a class, not a struct, because an instance corresponds to an external
object (the actual Node), so there's no semantic meaning to making multiple
copies.

Concrete implementations may include a "node in this machine" and a "remote
node elsewhere" a.k.a an image node.
'''

from enum import Enum
from openlcb.snip import SNIP
from openlcb.localeventstore import LocalEventStore


class Node:
    """Network node with an associated ID, SNIP, PIP set, and state.

    Args:
        nodeID (NodeID): The unique identifier for the node.
        snip (SNIP, optional): An optional SNIP instance associated with
            the node. Defaults to a new SNIP instance if not provided.
        pipSet (set[PIP], optional): A set of PIP enums associated with
            the node. Defaults to an empty set if not provided.

    Attributes:
        id (NodeID): The unique identifier for the node.
        snip (SNIP): The SNIP instance associated with the node.
        pipSet (set[PIP]): The set of PIP enums associated with the
            node.
        state (Node.State): The current state of the node, initialized
            to `Node.State.Uninitialized`.
        events (LocalEventStore): The store for local events associated
            with the node.
    """
    def __init__(self, nodeID, snip=None, pipSet=None):
        self.id = nodeID
        self.snip = snip
        if snip is None : self.snip = SNIP()
        self.pipSet = pipSet
        if pipSet is None : self.pipSet = set([])
        self.state = Node.State.Uninitialized
        self.events = LocalEventStore()

    def __str__(self):
        return "Node ("+str(self.id)+")"

    def name(self):
        return self.snip.userProvidedNodeName

    class State(Enum):
        Uninitialized = 1
        Initialized = 2

    def __eq__(lhs, rhs):
        '''Equality is defined on the NodeID only.'''
        if rhs is None:
            return False
        return lhs.id == rhs.id

    def __hash__(self):
        return hash(self.id)

    def __gt__(lhs, rhs):
        return lhs.id.nodeId > rhs.id.nodeId

    def __lt__(lhs, rhs):
        return lhs.id.nodeId < rhs.id.nodeId
