'''
#
#  DatagramService.swift
#  
#
#  Created by Bob Jacobsen on 6/1/22.
#
#/ Provide a service interface for reading and writing Datagrams.
#/ 
#/ Writes to remote node:
#/ - Create a ``DatagramWriteMemo`` and submit via ``sendDatagram(_:)``
#/ - Get an OK or NotOK callback
#/
#/ Reads from remote node:
#/  - One or more listeners register via ``registerDatagramReceivedListener(_:)``
#/  - Listeners are notified via call back
#/  - Exactly one should call ``positiveReplyToDatagram(_:flags:)`` or ``negativeReplyToDatagram(_:err:)`` before returning from listener
#/
#/ Implements `Processor`, should be fed as part of common execution
#/
#/ Handles link quiesce/restart so that higher level services don't have to.
#/    1) If there's an outstanding datagram reply with link restarts, resend it
#/    2) Once the link has been quiesced, datagrams are held until it's restarted
#/
'''    

from enum import Enum
import logging

from message import *
from mti import *
from nodeid import *

def defaultIgnoreReply(memo) :
    # default handling of reply does nothing
    pass

# Immutable memo carrying write request and two reply callbacks.
#
# Source is automatically this node.
class DatagramWriteMemo :
    
    def __init__(self, destID, data, okReply = defaultIgnoreReply, rejectedReply = defaultIgnoreReply) :
        self.destID = destID
        self.data = data
        self.okReply = okReply
        self.rejectedReply = rejectedReply
     
    def __eq__(lhs, rhs) :
        if lhs.destID != rhs.destID : return False
        if lhs.data != rhs.data : return False
        return True

# Immutable memo carrying read result.
#
# Destination of operations is automatically this node.
class DatagramReadMemo : 
    
    def __init__(self, srcID, data) :
        self.srcID = srcID
        self.data = data
    
    def __eq__(lhs, rhs) :
        if lhs.srcID != rhs.srcID : return False
        if lhs.data != rhs.data : return False
        return True
        


class DatagramService:
    # Known datagram protocol types
    class ProtocolID(Enum) :
        LogRequest      = 0x01
        LogReply        = 0x02

        MemoryOperation = 0x20

        RemoteButton    = 0x21
        Display         = 0x28
        TrainControl    = 0x30

        Unrecognized    = 0xFF # Not formally assigned

    def __init__(self, linkLayer) :
        self.linkLayer = linkLayer
        self.quiesced = False
        self.currentOutstandingMemo = None
        self.pendingWriteMemos = []
        self.listeners = []
   
    # Determine the protocol type of the content of the datagram.
    # 
    #   - Returns: 'Unrecognized' if there is no type specified, i.e. the datagram is empty
    def datagramType(self, data) :
        if len(data) == 0 : return DatagramService.ProtocolID.Unrecognized
        try : 
            retval = DatagramService.ProtocolID(data[0])
        except:
            return DatagramService.ProtocolID.Unrecognized
        if retval != None :
            return retval
        else :
            return DatagramService.ProtocolID.Unrecognized

    # check whether a message is addressed to a specific nodeID
    # Global messages return false: Not specifically addressed
    def checkDestID(self, message, nodeID) :
        return message.destination == nodeID

    # Queue a ``DatagramWriteMemo`` to send a datagram to another node on the network.
    def sendDatagram(self, memo) :
        # Make a record of memo for reply
        self.pendingWriteMemos.append(memo)
        
        # can only have one outstanding at a time, so check it there was already one there.
        if len(self.pendingWriteMemos) == 1 :
            self.sendDatagramMessage(memo)
    
    def sendDatagramMessage(self, memo) :
        # Send datagram message
        message = Message(MTI.Datagram, self.linkLayer.localNodeID, memo.destID, memo.data)
        self.linkLayer.sendMessage(message)
        self.currentOutstandingMemo = memo
    
    # Register a listener to be notified when each datagram arrives.
    #
    # One and only one listener should reply positively or negatively to the datagram and return true.
    def registerDatagramReceivedListener(self, listener) : 
        self.listeners.append(listener)
    
    def fireListeners(self, dg) :  # internal for testing
        replied = False
        for listener in self.listeners:
            replied = listener(dg) or replied    # order matters on that: Need to always make the call
        # If none of the listeners replied by now, send a negative reply
        if not replied :
            self.negativeReplyToDatagram(dg, 0x1042)  # “Not implemented, datagram type unknown” - permanent error

    
    # Processor entry point.
    # - Returns: Always false; a datagram doesn't mutate the node, it's the actions brought by that datagram that does.
    def process(self, message) : 
        # Check that it's to us or a global (for link layer up)
        if not (message.isGlobal() or self.checkDestID(message, self.linkLayer.localNodeID)) : return False 
        
        match message.mti :
            case MTI.Datagram :
                self.handleDatagram(message)
            case MTI.Datagram_Rejected :
                self.handleDatagramRejected(message)
            case MTI.Datagram_Received_OK :
                self.handleDatagramReceivedOK(message)
            case MTI.Link_Layer_Quiesce :
                self.handleLinkQuiesce(message)
            case MTI.Link_Layer_Restarted :
                self.handleLinkRestarted(message)
        return False
    
    def handleDatagram(self, message) :
        # create a read memo and pass to listeners
        memo = DatagramReadMemo(message.source, message.data)
        self.fireListeners(memo) # destination listener calls back to
                            # positiveReplyToDatagram/negativeReplyToDatagram before returning
    
    # OK reply to write
    def handleDatagramReceivedOK(self, message) :
        # match to the memo and remove from queue
        memo = self.matchToWriteMemo(message)
        
        # check of tracking logic
        if self.currentOutstandingMemo != memo :
            logging.error("Outstanding and replied-to memos don't match on OK reply")
        
        self.currentOutstandingMemo = None
        
        # fire the callback
        memo.okReply(memo)
        
        self.sendNextDatagramFromQueue()

    # Not OK reply to write
    def handleDatagramRejected(self, message) :
        # match to the memo and remove from queue
        memo = self.matchToWriteMemo(message)

        # check of tracking logic
        if self.currentOutstandingMemo != memo :
            logging.error("Outstanding and replied-to memos don't match on rejected")

        currentOutstandingMemo = None

        # fire the callback
        memo.rejectedReply(memo)

        self.sendNextDatagramFromQueue()
   
    # Link quiesced before outage: stop operation
    def handleLinkQuiesce(self, message) : 
        quiesced = true

    # Link restarted after outage: if write datagram(s) pending reply, resend them
    def handleLinkRestarted(self, message) :
        self.quiesced = False
        if self.currentOutstandingMemo != None :
            # there's a current outstanding memo to repeat
            logging.info("Retrying datagram after restart")
            self.sendDatagramMessage(self.currentOutstandingMemo)
            return
        else:
            # are there any queued datagrams? If so, send first
            if len(self.pendingWriteMemos) > 0 :
                self.sendNextDatagramFromQueue()
    
    def matchToWriteMemo(self, message):
        for memo in self.pendingWriteMemos :
            if memo.destID != message.source : break
            # remove the found element - might need a try/except on this
            index = self.pendingWriteMemos.index(memo)
            del self.pendingWriteMemos[index]

            return memo
            
        # did not find one
        logging.error("Did not match memo to message \(message)")
        return None  # this will prevent firther processing
    
    def sendNextDatagramFromQueue(self) :
        # is there a next datagram request?
        if len(self.pendingWriteMemos) > 0 :
            # yes, get it, process it
            memo = self.pendingWriteMemos[0]
            self.sendDatagramMessage(memo)
    
    # Send a positive reply to a received datagram.
    # - Parameters:
    #   - dg: Datagram memo being responded to.
    #   - flags: Flag byte to be returned to sender, see Datagram S&TN for meaning.
    def positiveReplyToDatagram(self, dg, flags = 0) :
        message = Message(MTI.Datagram_Received_OK, self.linkLayer.localNodeID, dg.srcID, [flags])
        self.linkLayer.sendMessage(message)
    
    # Send a negative reply to a received datagram.
    # - Parameters:
    #   - dg: Datagram memo being responded to.
    #   - err: Error code(s) to be returned to sender, see Datagram S&TN for meaning.
    def negativeReplyToDatagram(self, dg, err) :
        data0 = ((err >> 8 ) & 0xFF)
        data1 = (err & 0xFF)
        message = Message(MTI.Datagram_Rejected, self.linkLayer.localNodeID, dg.srcID, [data0, data1])
        self.linkLayer.sendMessage(message)
