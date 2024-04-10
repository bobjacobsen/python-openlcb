'''
based on TcpLink.swift

Created by Bob Jacobsen on 8/3/22.

Handles link-layer formatting and unformatting for native TCP links

Usually connected to a TCP socket connection.

Assembles messages parts, but does not break messages into parts.

'''

from openlcb.linklayer import LinkLayer
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.nodeid import NodeID

import logging
import time


class TcpLink(LinkLayer):
    """A TCP link layer.

    Attributes:
        accumulatedData (list): input accumulated until an entire message is
            present.

    Args:
        localNodeID (NodeID): The node ID of the Configuration Tool or other
            software-defined node connecting to the LCC network via TCP.
    """

    def __init__(self, localNodeID):
        # See class docstring for argument(s) and attributes.
        self.localNodeID = localNodeID
        self.linkCall = None
        self.accumulatedParts = {}
        self.nextInternallyAssignedNodeID = 1
        self.accumulatedData = []

    def linkPhysicalLayer(self, lpl):
        """Register the handler for when the layer is up.

        Args:
            lpl (function): A handler that accepts a bytes object, usually a
                socket connection send() method.
        """
        self.linkCall = lpl

    def receiveListener(self, inputData):  # [] input
        """Receives bytes from lower level
        and accumulates them into individual message parts.

        Args:
            inputData ([int]) : next chunk of the input stream
        """
        self.accumulatedData.extend(inputData)
        # Now check it if has one or more complete message.
        while len(self.accumulatedData) > 0 :
            # first, see if entire prefix is present
            if len(self.accumulatedData) < 17 :  # 2+3+6+6
                # not yet, wait for more
                return
            flags = (self.accumulatedData[0] << 8) | self.accumulatedData[1]
            length = (self.accumulatedData[2] << 16) | (self.accumulatedData[3] << 8) | self.accumulatedData[4]  # noqa: E501
            # check if entire message (part) is present
            if len(self.accumulatedData) < 5+length :
                # not yet, wait for more
                return

            # Check for message indicated bit
            if (self.accumulatedData[0] & 0x80) == 0x80:
                # we have a message (part)!  Forward for further processing
                self.receivedPart(self.accumulatedData[:5+length], flags,
                                  length)
            else:
                # We don't have definitions for link control messages
                # so log and ignore
                logging.info(
                    "Found a link control message"
                    " with flags 0x{:04X} length {}, ignoring"
                    .format(flags, length)
                )
            # drop that message (part)
            self.accumulatedData = self.accumulatedData[5+length:]
            # and repeat

    def receivedPart(self, messagePart, flags, length):
        """Receives message parts from receiveListener
        and groups them into single OpenLCB messages as needed

        Args:
            messagePart (int) : Raw message data. A single TCP-level message,
                which may include all or part of a single OpenLCB message.
        """
        # set the source NodeID from the data
        gatewayNodeID = NodeID(messagePart[5:11])

        # handle simplest case first - complete message
        if (flags & 0x00C0) == 0x00000 :
            self.forwardMessage(messagePart[17:], gatewayNodeID)
            return

        # need to accumulate
        # - can be first, middle or last, but not entire message
        key = gatewayNodeID   # do we need to have the capture time in here?
        if (flags & 0x00C0) == 0x040 :  # first
            # check for error
            if self.accumulatedParts.get(key) is not None :
                # this was a first, but shouldn't have been
                logging.warn("Found a first part from {}"
                             " while already accumulating"
                             "".format(gatewayNodeID))
                # start over
            # start accumulation
            self.accumulatedParts[key] = []
        # accumulate next part
        self.accumulatedParts[key].extend(messagePart[17:])
        # is the accumulation complete?
        if (flags & 0x00C0) == 0x0080 :  # first
            # yes, forward to upper layer
            messageBytes = self.accumulatedParts[key]
            self.forwardMessage(messageBytes, gatewayNodeID)
            # and start over
            del self.accumulatedParts[key]
        # wait for next part
        return

    def forwardMessage(self, messageBytes, gatewayNodeID) :  # not sure why gatewayNodeID useful here...  # noqa: E501
        """
        Receives single message from receivedPart, converts
        it in a Message object, and forwards to listeners

        Args:
            messageBytes ([int]) : the bytes making up a
                single OpenLCB message, starting with the MTI
        """
        # extract MTI
        mti = MTI((messageBytes[0] << 8) | messageBytes[1])
        # extract sourceNodeID
        sourceNodeID = NodeID(messageBytes[2:8])
        # if there a destination Node ID?
        destNodeID = None
        data = messageBytes[8:]
        if mti.addressPresent() :
            destNodeID = NodeID(messagePart[8:13])
            data = messagePart[14:]
        # and finally create the message
        message = Message(mti, sourceNodeID, destNodeID, data)
        # forward to listeners
        self.fireListeners(message)

    def linkUp(self):
        """
        Link started,  notify upper layers
        """
        msg = Message(MTI.Link_Layer_Up, NodeID(0), None, [])
        self.fireListeners(msg)

    def linkRestarted(self):
        """
        Send a LinkRestarted message upstream.
        """
        msg = Message(MTI.Link_Layer_Restarted, NodeID(0), None, [])
        self.fireListeners(msg)

    def linkDown(self):
        """
        Link dropped,  notify upper layers
        """
        msg = Message(MTI.Link_Layer_Down, NodeID(0), None, [])
        self.fireListeners(msg)

    def sendMessage(self, message):
        """
        The message level calls this with an OpenLCB
        message.  That is then converted to a byte
        stream and forwarded to the TCP socket layer.
        """

        mti = message.mti

        outputBytes = [0x80, 0x00]  # flags

        length = 12+2+6+len(message.data)
        if mti.addressPresent() : length = length+6

        l0 = (length & 0xFF0000) >> 16
        l1 = (length & 0xFF00) >> 8
        l2 = (length & 0xFF)
        outputBytes.extend([l0, l1, l2])

        outputBytes.extend(self.localNodeID.toArray())

        t = round(time.time() * 1000)
        t0 = (t & 0xFF0000000000) >> 40
        t1 = (t & 0xFF00000000) >> 32
        t2 = (t & 0xFF000000) >> 24
        t3 = (t & 0xFF0000) >> 16
        t4 = (t & 0xFF00) >> 8
        t5 = (t & 0xFF)
        outputBytes.extend([t0, t1, t2, t3, t4, t5])

        m0 = (mti.value & 0xFF00) >> 8
        m1 = (mti.value & 0xFF)
        outputBytes.extend([m0, m1])

        outputBytes.extend(message.source.toArray())

        if mti.addressPresent() :
            outputBytes.extend(message.destination.toArray())

        outputBytes.extend(message.data)

        self.linkCall(outputBytes)
