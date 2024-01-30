'''
based on Processor.swift

Created by Bob Jacobsen on 6/1/22.

Process an incoming message, adjusting state and replying as needed.

Acts on a specific node. Processors have no state of their own,
instead they work on the status of a provided node.  This allows
on processor struct to handle communications for multiple nodes.
'''

from openlcb.nodeid import NodeID


class Processor:
    # abstract method to be implemented belpw
    # accept a Message, adjust state as needed, possibly reply
    # Returns: True if the contents of the node changed in a way that should be published, i.e. a PIP, SNIP or event model change
    def process(self, message, node=None):
        pass

    # check whether a message came from a specific nodeID
    # arg can be either a Node or NodeID
    # internal
    def checkSourceID(self, message, arg):
        if isinstance(arg, NodeID):
            return message.source == arg
        else:
            # assuming type is Node
            return message.source == arg.id

    # check whether a message is addressed to a specific nodeID
    # Global messages return false: Not specifically addressed
    # internal
    def checkDestID(self, message, arg):
        if isinstance(arg, NodeID):
            return message.destination == arg
        else:  # assuming type is Node
            return message.destination == arg.id
