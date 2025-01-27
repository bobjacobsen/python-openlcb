'''
based on MemoryService.swift

Created by Bob Jacobsen on 6/1/22.

TODO: Read requests are serialized, but write requests are not yet

Datagram retry handles the link being queisced/restarted, so it's not
explicitly handled here.

Does memory read and write requests.

Reads and writes are limited to 64 bytes at a time.

To do memory write:
- Create a ``MemoryWriteMemo`` and submit via ``requestMemoryWrite(_:)``
- Wait for either okReply or rejectedReply call back.

To do memory read:
- Create a ``MemoryReadMemo`` and submit via ``requestMemoryRead(_:)``
- Wait for either dataReply or rejectedReply call back.
'''

import logging
from openlcb.datagramservice import (
    # DatagramReadMemo,
    DatagramWriteMemo,
    DatagramService,
)


class MemoryReadMemo:
    """Memo carries request and reply.

    Args:
        nodeID (NodeID): _description_
        size (int): _description_
        space (int): _description_
        address (int): _description_
        rejectedReply (Callable[MemoryReadMemo]): Called if reply
            indicates read attempt was rejected.
        dataReply (Callable[MemoryReadMemo]): Called if read response
            contains data (occurs after okReply which is handled by
            MemoryService).

    Attributes:
        data(bytearray): The data that was read.
    """
    def __init__(self, nodeID, size, space, address, rejectedReply, dataReply):
        # For args see class docstring.
        self.nodeID = nodeID
        self.size = size
        self.space = space
        self.address = address
        self.rejectedReply = rejectedReply
        self.dataReply = dataReply
        # for convenience, data can be added or updated after creation of the
        # memo
        self.data = bytearray()


class MemoryWriteMemo:
    """_summary_
    Args:
        nodeID (NodeID): Node for which write is requested
        okReply (Callable[MemoryWriteMemo]): Called if request was
            accepted (data written).
        rejectedReply (Callable[MemoryWriteMemo]): Called if request was
            rejected (data not written).
        size (int): _description_
        space (int): _description_
        address (int): _description_
        data (bytearray): The data to write
    """
    def __init__(self, nodeID, okReply, rejectedReply, size, space, address,
                 data):
        # For args see class docstring.
        self.nodeID = nodeID
        self.okReply = okReply
        self.rejectedReply = rejectedReply
        self.size = size  # max 64 bytes
        self.space = space
        self.address = address
        self.data = data


class MemoryService:
    """Manage memory read and write requests
    (64 bytes at a time).

    Args:
        service (DatagramService): See DatagramService.
    """

    def __init__(self, service):
        self.service = service
        self.readMemos = []
        self.writeMemos = []
        self.spaceLengthCallback = None

        # register to DatagramService to hear arriving datagrams
        self.service.registerDatagramReceivedListener(
            self.datagramReceivedListener
        )

    def spaceDecode(self, space):
        """convert from a space number to either

        Args:
            space (int): The memory space bytes from the packet

        Returns:
            tuple(bool, byte): (False, 1-3 for in command byte) :
                spaces 0xFF - 0xFD
                or (True, space number) : spaces 0 - 0xFC
                (NOTE: type of space may affect type of output)
        """
        # TODO: Maybe check type of space & raise TypeError if not
        #   something valid, whether byte, int, or what is ok [add
        #   more _description_ to space in docstring].
        if space >= 0xFD:
            return (False, space & 0x03)
        return (True, space)

    def requestMemoryRead(self, memo):
        '''Request a read operation start.

        - If okReply in the memo is triggered, it will be followed by a
          dataReply.

        - A rejectedReply will not be followed by a dataReply.

        Args:
            memo (MemoryReadMemo): Request to enqueue.
        '''
        # preserve the request
        self.readMemos.append(memo)

        if len(self.readMemos) == 1:
            self.requestMemoryReadNext(memo)

    def requestMemoryReadNext(self, memo):
        """send the read request

        Args:
            memo (MemoryReadMemo): Request to send.
        """
        byte6 = False
        flag = 0
        (byte6, flag) = self.spaceDecode(memo.space)
        spaceFlag = 0x40 if byte6 else (flag | 0x40)
        addr2 = ((memo.address >> 24) & 0xFF)
        addr3 = ((memo.address >> 16) & 0xFF)
        addr4 = ((memo.address >> 8) & 0xFF)
        addr5 = (memo.address & 0xFF)
        data = bytearray([
            DatagramService.ProtocolID.MemoryOperation.value, spaceFlag,
            addr2, addr3, addr4, addr5])
        # NOTE: list[int] is ok for bytearray extend (`+` requires cast)
        if byte6:
            data.extend([(memo.space & 0xFF)])
        data.extend([memo.size])
        dgWriteMemo = DatagramWriteMemo(memo.nodeID, data,
                                        self.receivedOkReplyToWrite)
        self.service.sendDatagram(dgWriteMemo)

    def receivedOkReplyToWrite(self, memo):
        '''Wait for following response to be returned via listener.
        This is normal.
        '''
        pass

    def datagramReceivedListener(self, dmemo):
        '''Process a datagram.

        Sends the positive reply and returns true if this is from our service.
        '''
        # node received a datagram, is it our service?
        if self.service.datagramType(dmemo.data) \
                != DatagramService.ProtocolID.MemoryOperation :
            return False

        # datagram must has a command value
        if len(dmemo.data) < 2:
            logging.error("Memory service datagram too short:"
                          " {}".format(dmemo.data.count))
            # TODO: ^ more necessary to show same output as Swift? Formerly:
            #   " \(dmemo.data.count, privacy: .public)")
            self.service.negativeReplyToDatagram(dmemo, 0x1041)
            return True  # error, but for our service; sent negative reply
        # Acknowledge the datagram
        self.service.positiveReplyToDatagram(dmemo, 0x0000)

        # decode if read, write or some other reply
        if dmemo.data[1] in (0x50, 0x51, 0x52, 0x53, 0x58, 0x59, 0x5A, 0x5B):
            # read or read-error reply

            # return data to requestor: first find matching memory read
            # memo, then reply
            for index in range(0, len(self.readMemos)):
                if self.readMemos[index].nodeID == dmemo.srcID:
                    tMemoryMemo = self.readMemos[index]
                    del self.readMemos[index]
                    # decode type of operation, hence offset for start of
                    # data
                    offset = 6
                    if dmemo.data[1] == 0x50 or dmemo.data[1] == 0x58:
                        offset = 7

                    # are there any additional requests queued to send?
                    if len(self.readMemos) > 0:
                        self.requestMemoryReadNext(self.readMemos[0])

                    # fill data for call-back to requestor
                    if len(dmemo.data) > offset:
                        tMemoryMemo.data = dmemo.data[offset:]

                    # check for read or read error reply
                    if (dmemo.data[1] & 0x08 == 0):
                        tMemoryMemo.dataReply(tMemoryMemo)
                    else:
                        tMemoryMemo.rejectedReply(tMemoryMemo)
                    break
        elif dmemo.data[1] in (0x10, 0x11, 0x12, 0x13, 0x18, 0x19, 0x1A, 0x1B):
            # write reply good, bad

            # return data to requestor: first find matching memory write
            # memo, then reply
            for index in range(0, len(self.writeMemos)):
                if self.writeMemos[index].nodeID == dmemo.srcID:
                    tMemoryMemo = self.writeMemos[index]
                    del self.writeMemos[index]
                    if dmemo.data[1] & 0x08 == 0 :
                        tMemoryMemo.okReply(tMemoryMemo)
                    else:
                        tMemoryMemo.rejectedReply(tMemoryMemo)
                    break
        elif dmemo.data[1] in (0x86, 0x87):  # Address Space Information Reply
            if self.spaceLengthCallback is None:
                logging.error("Address Space Information Reply"
                              " received with no callback")
                return True
            if dmemo.data[1] == 0x86:
                # not present
                self.spaceLengthCallback(-1)
                self.spaceLengthCallback = None
                return True
            # normal reply
            address = ((int(dmemo.data[3]) << 24)
                       + (int(dmemo.data[4]) << 16)
                       + (int(dmemo.data[5]) << 8)
                       + int(dmemo.data[6]))
            self.spaceLengthCallback(address)
            self.spaceLengthCallback = None
        else:
            logging.error("Did not expect reply of type 0x{:02X}"
                          "".format(dmemo.data[1]))

        return True

    def requestMemoryWrite(self, memo):
        """Request memory write.

        Args:
            memo (MemoryWriteMemo): information to send
        """
        # preserve the request
        self.writeMemos.append(memo)
        # create & send a write datagram
        byte6 = False
        flag = 0
        (byte6, flag) = self.spaceDecode(memo.space)
        spaceFlag = 0x00 if byte6 else (flag | 0x00)
        addr2 = ((memo.address >> 24) & 0xFF)
        addr3 = ((memo.address >> 16) & 0xFF)
        addr4 = ((memo.address >> 8) & 0xFF)
        addr5 = (memo.address & 0xFF)
        data = bytearray([
            DatagramService.ProtocolID.MemoryOperation.value, spaceFlag,
            addr2, addr3, addr4, addr5
        ])
        if byte6:
            data.extend([(memo.space & 0xFF)])
        data.extend(memo.data)
        dgWriteMemo = DatagramWriteMemo(memo.nodeID, data)
        self.service.sendDatagram(dgWriteMemo)

    def requestSpaceLength(self, space, nodeID, callback):
        """Request the length of a specific memory space
        from a remote node.

        Args:
            space (int): (See DatagramWriteMemo)
            nodeID (NodeID): remote node ID
            callback (Callable[int]): A function that can receive the
                length of the memory space.
        """
        if self.spaceLengthCallback is not None:
            logging.error("Overlapping calls to requestSpaceLength")
            return
        self.spaceLengthCallback = callback
        # send request
        dgReqMemo = DatagramWriteMemo(
            nodeID,
            [DatagramService.ProtocolID.MemoryOperation.value, 0x84, space]
        )
        self.service.sendDatagram(dgReqMemo)

    def arrayToInt(self, data):
        """Convert an array in MSB-first order to an integer

        Args:
            data (Union[bytes,bytearray,list[int]]): MSB-first order
                encoded 32-bit int

        Returns:
            int: The converted data as a number.
        """
        result = 0
        for index in range(0, len(data)):
            result = result << 8
            result = result | data[index]
        return result

    def arrayToUInt64(self, data):
        """Parse a MSB-first order 64-bit integer
        (Python auto-sizes int, so this is same as arrayToInt).
        """
        return self.arrayToInt(data)

    @staticmethod
    def arrayToString(data, length):
        """Decode utf-8 bytes to string
        up to the 1st zero byte or given length,
        whichever is fewer characters.

        Args:
            data (Union[bytearray, bytes]): A string encoded as bytes.
            length (int): The used length the data.

        Returns:
            str: Data decoded as text.
        """
        zeroIndex = len(data)
        try:
            temp = data.index(0)
            zeroIndex = temp
        except KeyboardInterrupt:
            raise
        except:
            pass

        byteCount = min(zeroIndex, length)

        if byteCount == 0:
            return ""

        result = data[:byteCount].decode('utf-8')
        return result

    @staticmethod
    def intToArray(value, length):
        """Convert an integer into an array of given length

        Args:
            value (int): any value
            length (int): Byte count (1, 2, 4, or 8).

        Returns:
            bytearray: The value encoded in big-endian format.
        """
        if value >= (1 << (length * 8)):  # TODO: ? also exclude value < 0 ?
            raise ValueError("Value {} cannot fit in {} bytes."
                             .format(value, length))
        if length == 1:
            return bytearray([
                (value & 0xff)
            ])
        if length == 2:
            return bytearray([
                ((value >> 8) & 0xff), (value & 0xff)
            ])
        if length == 4:
            return bytearray([
                ((value >> 24) & 0xff), ((value >> 16) & 0xff),
                ((value >> 8) & 0xff),  (value & 0xff)
            ])
        if length == 8:
            return bytearray([
                ((value >> 56) & 0xff), ((value >> 48) & 0xff),
                ((value >> 40) & 0xff), ((value >> 32) & 0xff),
                ((value >> 24) & 0xff), ((value >> 16) & 0xff),
                ((value >> 8) & 0xff), (value & 0xff)
            ])
        logging.error("integer length {} is not implemented.".format(length))
        return bytearray()

    @staticmethod
    def uInt64ToArray(value, length):
        '''Convert a 64-bit integer into an array of given length
        (Python auto-sizes int, so this is same as intToArray)
        '''
        return MemoryService.intToArray(value, length)

    @staticmethod
    def stringToArray(value, length):
        '''Converts a string to an array of given length
        padding with 0 bytes as needed
        '''
        strToUInt8 = value.encode('utf-8')
        byteCount = min(length, len(strToUInt8))
        # convert to bytearray since bytes is immutable:
        contentPart = bytearray(strToUInt8[:byteCount])
        if len(contentPart) >= length:
            if len(contentPart) > length:
                logging.warning(
                    "MemoryService stringToArray: len(value)=={}"
                    " exceeds length {}".format(len(value), length))
                # TODO: Truncate (or is any length ok for the caller)?
            return contentPart
        # list[int] is compatible bytearray extend but not `+` so cast
        #   to bytearray after getting list[int] of remaining length:
        padding = bytearray([0] * (length-len(contentPart)))
        return contentPart + padding
