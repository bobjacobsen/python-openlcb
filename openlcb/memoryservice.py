'''#
#  MemoryService.swift
#  
#
#  Created by Bob Jacobsen on 6/1/22.
#

# TODO: Read requests are serialized, but write requests are not yet
# Datagram retry handles the link being queisced/restarted, so it's not explicitly handled here.

# Does memory read and write requests.
#
# Reads and writes are limited to 64 bytes at a time.
#
# To do memory write:
# - Create a ``MemoryWriteMemo`` and submit via ``requestMemoryWrite(_:)``
# - Wait for either okReply or rejectedReply call back.
#
# To do memory read:
# - Create a ``MemoryReadMemo`` and submit via ``requestMemoryRead(_:)``
# - Wait for either dataReply or rejectedReply call back.
#
'''

import logging
from datagramservice import *

# Memo carries request and reply
class MemoryReadMemo :
    def __init__(self, nodeID, size, space, address, rejectedReply, dataReply) :
        self.nodeID = nodeID
        self.size = size
        self.space = space
        self.address = address
        self.rejectedReply = rejectedReply
        self.dataReply = dataReply
        # for convenience, data can be added or updated after creation of the memo
        self.data = []

class MemoryWriteMemo :
    def __init__(self, nodeID, okReply, rejectedReply, size, space, address, data) :
        #/ Node from which write is requested
        self.nodeID = nodeID
        self.okReply = okReply
        self.rejectedReply = rejectedReply
        self.size = size # max 64 bytes
        self.space = space
        self.address = address
        self.data  = data

class MemoryService :
    
    def __init__(self, service) :
        self.service = service
        self.readMemos = []
        self.writeMemos = []
        self.spaceLengthCallback = None

        # register to DatagramService to hear arriving datagrams
        self.service.registerDatagramReceivedListener(self.datagramReceivedListener)
    
    # convert from a space number to either
    # (false, 1-3 for in command byte) : spaces 0xFF - 0xFD
    # (true, space number) : spaces 0 - 0xFC
    def spaceDecode(self, space) :
        if space >= 0xFD :
            return (False, space&0x03)
        else :
            return (True, space)

    
    #/ Request a read operation start.
    #/
    #/ If okReply in the memo is triggered, it will be followed by a dataReply.
    #/ A rejectedReply will not be followed by a dataReply.
    def requestMemoryRead(self, memo) :
        # preserve the request
        self.readMemos.append(memo)
        
        if len(self.readMemos) == 1 :
            self.requestMemoryReadNext(memo)
    
    def requestMemoryReadNext(self, memo) :
        # send the read request
        byte6 = False
        flag = 0
        (byte6, flag) = self.spaceDecode(memo.space)
        spaceFlag = 0x40 if byte6 else (flag | 0x40)
        addr2 = ( (memo.address >> 24) & 0xFF )
        addr3 = ( (memo.address >> 16) & 0xFF )
        addr4 = ( (memo.address >>  8) & 0xFF )
        addr5 = ( memo.address & 0xFF )
        data  = [DatagramService.ProtocolID.MemoryOperation.value, spaceFlag, addr2,addr3,addr4,addr5]
        if (byte6) :
            data.extend([(memo.space & 0xFF)])
        data.extend([memo.size])
        dgWriteMemo = DatagramWriteMemo(memo.nodeID, data, self.receivedOkReplyToWrite)
        self.service.sendDatagram(dgWriteMemo)
    
    def receivedOkReplyToWrite(self, memo) :
        # this is normal.  Wait for following response to be returned via listener
        pass

    # process a datagram.  Sends the positive reply and returns true iff this is from our service.
    def datagramReceivedListener(self, dmemo) : 
        # node received a datagram, is it our service?
        if self.service.datagramType(dmemo.data) != DatagramService.ProtocolID.MemoryOperation:
            return False

        # datagram must has a command value
        if len(dmemo.data) < 2 :
            logging.error("Memory service datagram too short: \(dmemo.data.count, privacy: .public)")
            self.service.negativeReplyToDatagram(dmemo, 0x1041)
            return True;  # error, but for our service; sent negative reply
        # Acknowledge the datagram
        self.service.positiveReplyToDatagram(dmemo, 0x0000)
        
        # decode if read, write or some other reply
        match dmemo.data[1] :
            case 0x50 | 0x51 | 0x52 | 0x53 | 0x58 | 0x59 | 0x5A | 0x5B : # read or read-error reply
                # return data to requestor: first find matching memory read memo, then reply
                for index in range( 0, len(self.readMemos)) :
                    if self.readMemos[index].nodeID == dmemo.srcID :
                        tMemoryMemo = self.readMemos[index]
                        del self.readMemos[index]
                        # decode type of operation, hence offset for start of data
                        offset = 6
                        if dmemo.data[1] == 0x50 or dmemo.data[1] == 0x58 :
                            offset = 7
                    
                        # are there any additional requests queued to send?
                        if len(self.readMemos) > 0 :
                            self.requestMemoryReadNext(self.readMemos[0])
                    
                        # fill data for call-back to requestor
                        if len(dmemo.data) > offset :
                            tMemoryMemo.data = dmemo.data[offset:]
                    
                        # check for read or read error reply
                        if (dmemo.data[1] & 0x08 == 0) :
                            tMemoryMemo.dataReply(tMemoryMemo)
                        else :
                            tMemoryMemo.rejectedReply(tMemoryMemo)
                        break
            case 0x10 | 0x11 | 0x12 | 0x13 | 0x18 | 0x19 | 0x1A | 0x1B : # write reply good, bad
                # return data to requestor: first find matching memory write memo, then reply
                for index in range(0, len(self.writeMemos)) :
                    if self.writeMemos[index].nodeID == dmemo.srcID :
                        tMemoryMemo = self.writeMemos[index]
                        del self.writeMemos[index]
                        if (dmemo.data[1] & 0x08 == 0) :
                            tMemoryMemo.okReply(tMemoryMemo)
                        else :
                            tMemoryMemo.rejectedReply(tMemoryMemo)
                        break

            case 0x86 | 0x87 : # Address Space Information Reply
                if self.spaceLengthCallback == None :
                    logging.error("Address Space Information Reply received with no callback")
                    return True
                if dmemo.data[1] == 0x86 :
                    # not present
                    spaceLengthCallback(-1)
                    spaceLengthCallback = None
                    return True
                # normal reply
                address = Int(dmemo.data[3]) << 24 + \
                            Int(dmemo.data[4]) << 16 + \
                            Int(dmemo.data[5]) << 8 + \
                            Int(dmemo.data[6])
                spaceLengthCallback(address)
                spaceLengthCallback = None

            case _ :
                logging.error("Did not expect reply of type 0x{:02X}".format(dmemo.data[1]))
        
        return True
    
    def requestMemoryWrite(self, memo) :
        # preserve the request
        self.writeMemos.append(memo)
        # create & send a write datagram
        byte6 = False
        flag = 0
        (byte6, flag) = self.spaceDecode(memo.space)
        spaceFlag = 0x00 if byte6 else (flag | 0x00)
        addr2 = ( (memo.address >> 24) & 0xFF )
        addr3 = ( (memo.address >> 16) & 0xFF )
        addr4 = ( (memo.address >>  8) & 0xFF )
        addr5 = ( memo.address & 0xFF )
        data = [DatagramService.ProtocolID.MemoryOperation.value, spaceFlag, addr2,addr3,addr4,addr5]
        if (byte6) :
            data.extend([(memo.space & 0xFF)])
        data.extend(memo.data)
        dgWriteMemo = DatagramWriteMemo(memo.nodeID, data)
        self.service.sendDatagram(dgWriteMemo)
        
    #/ Request the length of a specific memory space from a remote node.
    def requestSpaceLength(self, space, nodeID, callback) :
        if self.spaceLengthCallback != None :
            logging.error("Overlapping calls to requestSpaceLength")
            return
        self.spaceLengthCallback = callback
        # send request
        dgReqMemo = DatagramWriteMemo(nodeID, [DatagramService.ProtocolID.MemoryOperation.rawValue, 0x84, space])
        service.sendDatagram(dgReqMemo)
    
    # converts an array in MSB-first order to an integer
    def arrayToInt(self, data) : 
        result = 0
        for index in range(0, length-1) :
            result = result << 8
            result = result | data[index]
        return result
    
    # converts an array in MSB-first order to a 64-bit integer
    def arrayToUInt64(self, data) :
        result : UInt64 = 0
        for index in range(0, length-1) :
            result = result << 8
            result = result | data[index]
        return result
    
    # converts and array to a string up to the 1st zero byte or given length
    def arrayToString(self, data, length) :
        zeroIndex = len(data)
        try:
            temp = data.index(0)
            zeroIndex = temp
        except:
            pass
            
        byteCount = min(zeroIndex, length )

        if (byteCount == 0) :
            return ""
        
        result = ''.join([chr(i) for i in data[:byteCount]])
        return result

    def intToArray(self, value, length) : 
        match length :
            case 1:
                return [(value&0xff)]
            case 2:
                return [((value>>8 )&0xff), (value&0xff)]
            case 4:
                return [((value>>24)&0xff), ((value>>16)&0xff),
                        ((value>>8)&0xff),  (value&0xff)]
            case 8:
                return [((value>>56)&0xff), ((value>>48)&0xff),
                        ((value>>40)&0xff), ((value>>32)&0xff),
                        ((value>>24)&0xff), ((value>>16)&0xff),
                        ((value>>8 )&0xff), (value&0xff)]
            case _ :
                return []
    
    # converts a 64-bit integer into an array of given length
    def uInt64ToArray(self, value, length) :
        match length :
            case 1:
                return [(value&0xff)]
            case 2:
                return [((value>>8 )&0xff), (value&0xff)]
            case 4:
                return [((value>>24)&0xff), ((value>>16)&0xff),
                        ((value>>8)&0xff),  (value&0xff)]
            case 8:
                return [((value>>56)&0xff), ((value>>48)&0xff),
                        ((value>>40)&0xff), ((value>>32)&0xff),
                        ((value>>24)&0xff), ((value>>16)&0xff),
                        ((value>>8 )&0xff), (value&0xff)]
            case _:
                return []

    #/ Converts a string to an array of given length, padding with 0 bytes as needed
    def stringToArray(self, value, length) :
        strToUInt8 = value.encode('ascii')
        byteCount = min(length, len(strToUInt8))
        contentPart = list(strToUInt8[:byteCount])
        padding = [0]*length
        contentPart.extend(padding)
        
        return contentPart[:length]

