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

    def process(self, message, node=None):
        """abstract method to be implemented below
        Accept a Message, adjust state as needed, possibly reply.

        Args:
            message (Message): Message to process.
            node (Optional[_type_]): _description_. Defaults to None.

        Returns:
            bool: True if the contents of the node changed in a way that should
                be published, i.e. a PIP, SNIP or event model change
        """
        pass

    # TODO: so maybe add _ to beginning of method names marked "# internal"

    # internal
    def checkSourceID(self, message, arg):
        """check whether a message came from a specific nodeID

        Args:
            message (Message): A message.
            arg (Union[NodeID,int]): NodeID or Node ID int to compare against
                message.source.

        Returns:
            bool: Whether the source of message is the given Node ID.
        """
        if isinstance(arg, NodeID):
            return message.source == arg
        else:
            # assuming type is Node
            return message.source == arg.id

    # internal
    def checkDestID(self, message, arg):
        """check whether a message is addressed to a specific nodeID

        Args:
            message (Message): A Message.
            arg (Union[NodeID,int]): A Node ID.

        Returns:
            bool: Whether the message ID matches the arg. Global messages
                return False: Not specifically addressed.
        """
        if isinstance(arg, NodeID):
            return message.destination == arg
        else:  # assuming type is Node
            return message.destination == arg.id
