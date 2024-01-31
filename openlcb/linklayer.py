'''
based on LinkLayer.swift

Created by Bob Jacobsen on 6/1/22.

Handles link-layer formatting and unformatting for a particular kind of
communications link.

Nodes are handled in one of two ways:
- "Own Node" - this is a node resident within the program
- "Remote Node" - this is a node outside the program

This is a class, not a struct, because an instance corresponds to an external
object (the actual link implementation), so there's no semantic meaning to
making multiple copies of a single object.
'''

from enum import Enum
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.nodeid import NodeID


class LinkLayer:

    class State(Enum):
        Initial = 1,  # a special case of .Inhibited where init hasn't started
        Inhibited = 2,
        Permitted = 3

    def __init__(self, localNodeID):
        self.localNodeID = localNodeID

    def sendMessage(self, msg):  # this is the basic abstract interface
        pass

    def registerMessageReceivedListener(self, listener):
        self.listeners.append(listener)

    listeners = []  # local list of listener callbacks

    def fireListeners(self, msg):
        for listener in self.listeners:
            listener(msg)

    # invoked when the link layer comes up and down
    def linkStateChange(self, state):  # state is of the State enum
        if state == LinkLayer.State.Permitted:
            msg = Message(MTI.Link_Layer_Up, NodeID(0), None, [])
        else:
            msg = Message(MTI.Link_Layer_Down, NodeID(0), None, [])
        self.fireListeners(msg)
