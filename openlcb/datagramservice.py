'''
based on DatagramService.swift

Created by Bob Jacobsen on 6/1/22.

Provide a service interface for reading and writing Datagrams.

Writes to remote node:
- Create a ``DatagramSendMemo`` and submit via ``sendDatagram(_:)``
- Get an OK or NotOK callback

Reads from remote node:
- One or more listeners register via ``registerDatagramReceivedListener(_:)``
- Listeners are notified via call back
- Exactly one should call `positiveReplyToDatagram(_:flags:)` or
  `negativeReplyToDatagram(_:err:)` before returning from listener

Implements `Processor`, should be fed as part of common execution

Handles link quiesce/restart so that higher level services don't have to.
1) If there's an outstanding datagram reply with link restarts, resend it
2) Once the link has been quiesced, datagrams are held until it's restarted
'''

from enum import Enum
from logging import getLogger
from typing import (
    Any,
    Callable,
    List,  # in case list doesn't support `[` in this Python version
    Union,  # in case `|` doesn't support 'type' in this Python version
)

from openlcb.linklayer import LinkLayer
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.nodeid import NodeID

logger = getLogger(__name__)


def defaultIgnoreReply(memo: Union[Any, None]):
    # ^ DatagramSendMemo is the type, but that is not defined yet
    '''default handling of reply does nothing'''
    pass


class DatagramSendMemo:
    '''Immutable memo carrying write request and two reply callbacks
    (In this context "Write" means sent to other node, even if
    associated with a MemoryReadMemo).
    Source is automatically this node.
    '''
    def __init__(self, destID: NodeID, data,
                 okReply=defaultIgnoreReply,
                 rejectedReply=defaultIgnoreReply):
        # type: (NodeID, bytearray, Callable[[Union[DatagramSendMemo, None]], None], Callable[[Union[DatagramSendMemo, None]], None]) -> None  # noqa: E501
        assert isinstance(destID, NodeID)
        self.destID = destID
        # NOTE: No srcID since always from this node ("Write" means send
        #   to other node, even if carrying a memory read request)
        if not isinstance(data, bytearray):
            raise TypeError("Expected bytearray (formerly list[int]), got {}"
                            .format(type(data).__name__))
        self.data: bytearray = data
        self.okReply: Callable[[Union[DatagramSendMemo, None]], None] = okReply  # noqa: E501
        self.rejectedReply: Callable[[Union[DatagramSendMemo, None]], None] = rejectedReply  # noqa: E501

    def __eq__(lhs, rhs):
        if lhs.destID != rhs.destID:
            return False
        if lhs.data != rhs.data:
            return False
        return True


class DatagramReceiveMemo:
    '''Immutable memo carrying read result
    (In this context "Read" means received from other node,
    *not* associated with a MemoryReadMemo which, however, may be what
    the sender is doing, but in that context "Read" means something
    different).
    Destination of operations is automatically this node.
    '''
    def __init__(self, srcID: NodeID, data: bytearray):
        self.srcID: NodeID = srcID
        self.data: bytearray = data

    def __eq__(lhs, rhs):
        if lhs.srcID != rhs.srcID:
            return False
        if lhs.data != rhs.data:
            return False
        return True


class DatagramService:
    """Known datagram protocol types

    Args:
        linkLayer (CanLink): Could actually be any link layer such as
            LinkMockLayer (for testing) or CanLink.

    Attributes:
        pendingSendMemos: (formerly pendingWriteMemos) These are written
            to the port, but a MemorySendMemo may be associated with a
            MemoryReadMemo since the device instantiating the service is
            making the request; or may be used to send replies as well
            (See where MemoryService instantiates any MemorySendMemo to
            respond to space info request especially when the node
            instantiating MemoryService is a node other than a
            Configuration Tool).
    """

    class ProtocolID(Enum):
        LogRequest      = 0x01
        LogReply        = 0x02

        MemoryOperation = 0x20

        RemoteButton    = 0x21
        Display         = 0x28
        TrainControl    = 0x30

        Unrecognized    = 0xFF  # Not formally assigned

    def __init__(self, linkLayer: LinkLayer):
        self.linkLayer: LinkLayer = linkLayer
        self.quiesced: bool = False
        self.currentOutstandingMemo: Union[DatagramSendMemo, None] = None  # noqa: E501
        self.pendingSendMemos: List[DatagramSendMemo] = []
        self._datagramReceivedListeners: List[Callable[[DatagramReceiveMemo], bool]] = []  # noqa: E501

    def datagramType(self, data: Union[bytearray, List[int]]):
        """Determine the protocol type of the content of the datagram.

        Args:
            data (bytearray): datagram payload

        Returns:
            DatagramService.ProtocolID: A detected protocol ID, or
                ProtocolID.Unrecognized if there is no type specified, i.e. the
                datagram is empty
        """
        if len(data) == 0:
            return DatagramService.ProtocolID.Unrecognized
        try:
            retval = DatagramService.ProtocolID(data[0])
        except KeyboardInterrupt:
            raise
        except:
            return DatagramService.ProtocolID.Unrecognized
        if retval is not None:
            return retval
        else:
            return DatagramService.ProtocolID.Unrecognized

    def checkDestID(self, message, nodeID: NodeID):
        '''check whether a message is addressed to a specific nodeID

        Returns:
            bool: Global messages return False: Not specifically addressed
        '''
        assert isinstance(nodeID, NodeID)
        return message.destination == nodeID

    def sendDatagram(self, memo: DatagramSendMemo):
        '''Queue a ``DatagramSendMemo`` to send a datagram to another node
        on the network.
        '''
        # Make a record of memo for reply
        self.pendingSendMemos.append(memo)

        # can only have one outstanding at a time, so check it there was
        # already one there.
        if len(self.pendingSendMemos) == 1:
            self.sendDatagramMessage(memo)

    def sendDatagramMessage(self, memo: DatagramSendMemo):
        '''Send datagram message'''
        message = Message(MTI.Datagram, self.linkLayer.localNodeID,
                          memo.destID, memo.data)
        self.linkLayer.sendMessage(message)
        self.currentOutstandingMemo = memo

    def registerDatagramReceivedListener(
            self, listener: Callable[[DatagramReceiveMemo], bool]):
        '''Register a listener to be notified when each datagram arrives.

        One and only one listener should reply positively or negatively to the
        datagram and return true.

        Args:
            listener (Callable): A function that accepts a DatagramReceiveMemo
                as an argument.
        '''
        logger.debug(
            "REGISTERING registerDatagramReceivedListener listener"
            f" {len(self._datagramReceivedListeners) + 1}")
        self._datagramReceivedListeners.append(listener)

    def fireDatagramReceived(self, dg: DatagramReceiveMemo):  # internal for tests
        """Fire *datagram received* listeners."""
        logger.debug(
            f"FIRING listeners for datagram from {dg.srcID},"
            f" size={len(dg.data)}")
        replied = False
        for listener in self._datagramReceivedListeners:
            replied = listener(dg) or replied
            # ^ order matters on that: Need to always make the call
        # If none of the listeners replied by now, send a negative reply
        if not replied:
            self.negativeReplyToDatagram(dg, 0x1042)
            # "Not implemented, datagram type unknown" - permanent error

    def process(self, message: Message):
        '''Processor entry point.
        Args:
            message (Message): Message that could be from anywhere,
                internal or from the network, since this method is
                typically called by CanLink's fireMessageReceived (If
                registered by instantiating DatagramService
                automatically using OpenLCBNetwork or calling
                canLink.registerMessageReceivedListener manually).

        Returns:
            bool: Always False; a datagram doesn't mutate the node, it's the
                actions brought by that datagram that does.
        '''
        # Check that it's to us or a global (for link layer up)
        if not (message.isGlobal()
                or self.checkDestID(message, self.linkLayer.localNodeID)):
            return False

        if message.mti == MTI.Datagram:
            self.handleDatagram(message)
        elif message.mti == MTI.Datagram_Rejected:
            self.handleDatagramRejected(message)
        elif message.mti == MTI.Datagram_Received_OK:
            self.handleDatagramReceivedOK(message)
        elif message.mti == MTI.Link_Layer_Quiesce:
            self.handleLinkQuiesce(message)
        elif message.mti == MTI.Link_Layer_Restarted:
            self.handleLinkRestarted(message)
        return False

    def handleDatagram(self, message: Message):
        '''create a read memo and pass to listeners'''
        memo = DatagramReceiveMemo(message.source, message.data)
        self.fireDatagramReceived(memo)
        # ^ destination listener calls back to
        #   positiveReplyToDatagram/negativeReplyToDatagram before returning

    def handleDatagramReceivedOK(self, message: Message):
        '''OK reply to write'''
        # match to the memo and remove from queue
        memo = self.matchToWriteMemo(message)  # type: DatagramSendMemo|None

        # check for whether a match was found, indicating this was for us
        if memo is None:
            logger.debug(
                f"Unrelated OK reply discarded: from"
                f" {message.source} to {message.destination}")
            return

        # check of tracking logic
        if self.currentOutstandingMemo != memo:
            logger.error(
                "Outstanding and replied-to memos don't match on OK reply"
            )

        self.currentOutstandingMemo = None

        # fire the callback
        memo.okReply(memo)

        self.sendNextDatagramFromQueue()

    def handleDatagramRejected(self, message: Message):
        '''Not OK reply to write'''
        # match to the memo and remove from queue
        memo = self.matchToWriteMemo(message)

        # check for whether a match was found, indicating this was for us
        if memo is None:
            logger.debug(
                f"Unrelated Rejected reply discarded: from"
                f" {message.source} to {message.destination}")
            return

        # check of tracking logic
        if self.currentOutstandingMemo != memo:
            logger.error(
                "Outstanding and replied-to memos don't match on rejected"
            )

        self.currentOutstandingMemo = None

        # fire the callback
        memo.rejectedReply(memo)

        self.sendNextDatagramFromQueue()

    def handleLinkQuiesce(self, message: Message):
        '''Link quiesced before outage: stop operation'''
        self.quiesced = True

    def handleLinkRestarted(self, message: Message):
        '''Link restarted after outage:
        if write datagram(s) pending reply, resend them
        '''
        self.quiesced = False
        if self.currentOutstandingMemo is not None:
            # there's a current outstanding memo to repeat
            logger.info("Retrying datagram after restart")
            self.sendDatagramMessage(self.currentOutstandingMemo)
            return
        else:
            # are there any queued datagrams? If so, send first
            if len(self.pendingSendMemos) > 0:
                self.sendNextDatagramFromQueue()

    def matchToWriteMemo(self, message: Message):
        for memo in self.pendingSendMemos:
            if memo.destID != message.source:
                continue  # keep looking
            # remove the found element - might need a try/except on this
            index = self.pendingSendMemos.index(memo)
            del self.pendingSendMemos[index]

            return memo

        # did not find one
        logger.error("Did not match memo to message {}"
                     .format(message))
        return None  # this will prevent further processing

    def sendNextDatagramFromQueue(self):
        # is there a next datagram request?
        if len(self.pendingSendMemos) > 0:
            # yes, get it, process it
            memo = self.pendingSendMemos[0]
            self.sendDatagramMessage(memo)

    def positiveReplyToDatagram(self, dg: DatagramReceiveMemo, flags: int = 0):
        """Send a positive reply to a received datagram.

        Args:
            dg (DatagramReceiveMemo): Datagram memo being responded to.
            flags (Optional[int]): Flag byte to be returned to sender, see
                Datagram Standard & Technical Note for meaning. Defaults to 0.
        """
        message = Message(MTI.Datagram_Received_OK, self.linkLayer.localNodeID,
                          dg.srcID, bytearray([flags]))
        self.linkLayer.sendMessage(message)

    def negativeReplyToDatagram(self, dg: DatagramReceiveMemo, err: int):
        """Send a negative reply to a received datagram.

        Args:
            dg (DatagramReceiveMemo): Datagram memo being responded to.
            err (int): Error code(s) to be returned to sender,
                see Datagram Standard & Technical Note for meaning.
        """
        data0 = ((err >> 8) & 0xFF)
        data1 = (err & 0xFF)
        message = Message(MTI.Datagram_Rejected, self.linkLayer.localNodeID,
                          dg.srcID, bytearray([data0, data1]))
        self.linkLayer.sendMessage(message)
