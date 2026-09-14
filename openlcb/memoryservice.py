'''
based on MemoryService.swift

Created by Bob Jacobsen on 6/1/22.

TODO: Read requests are serialized, but write requests are not yet

Datagram retry handles the link being quiesced/restarted, so it's not
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

from enum import Enum
from logging import getLogger
import struct
from typing import (
    Callable,
    List,
    Optional,  # in case list doesn't support `[` in this Python version
    Union,  # in case `|` doesn't support 'type' in this Python version
)

from openlcb import (
    emit_cast,
)
from openlcb.datagramservice import (
    # DatagramReceiveMemo,
    DatagramReceiveMemo,
    DatagramSendMemo,
    DatagramService,
)
from openlcb.convert import Convert
# from openlcb.localnode import LocalNode  # circular import
from openlcb.memoryconfigurationheader import MemoryConfigurationHeader
from openlcb.memoryspace import MemorySpace
from openlcb.memoryspaceindex import MemorySpaceIndex
from openlcb.memorymanager import MemoryManager
from openlcb.nodeid import NodeID

logger = getLogger(__name__)


class MCOp(Enum):
    """Byte 1 values where first 6 bits are unique *or*
    last 2 bits do *not* have a separate meaning
    (first 6 bits can't be used in isolation to determine
    meaning, but first 6 bits typically imply a set of
    more loosely related commands).
    - Use datagram memo's `data[1] & MCOpMasks.Default` (use
      "bitwise and" with the 6-high-bit mask) to get first 6 bits, which
      can be used as a param for fromNumber (For operations where last 2
      bits do not have a separate meaning, do not use the 6-high-bit
      mask).
    - Byte 0 is 0x20 for Memory Configuration.
    - Byte 1 values not in here (not masked) are in TWO_BIT_PARAMS
      and/or OP_FAILURE_BYTES.
      - Any value in here indicating *failure*, whether or not a key in
        TWO_BIT_PARAMS, is a key in OP_FAILURE_BYTES.
    - For a full understanding of how the Memory Configuration protocol
      constants are systematized, See testProtocolGroupUniqueness and/or
      the constant dicts using these values as keys.
    """
    Read_Command = 0x40  # 01000000
    Read_Reply = 0x50    # 01010000
    Read_Reply_Failure = 0x58  # 01011000; See OP_FAILURE_BYTES
    Read_Stream_Command = 0x60  # 01100000
    Read_Stream_Reply = 0x70  # 01110000
    Read_Stream_Reply_Failure = 0x78  # 01111000; See OP_FAILURE_BYTES
    Write_Command = 0x00
    Write_Reply = 0x10  # 00010000
    # or                  00010001 (0x11) and so on
    Write_Reply_Failure = 0x18  # 00011000; See OP_FAILURE_BYTES
    Write_Under_Mask_Command = 0x08  # 00001000
    Write_Stream_Command = 0x20  # 01000000
    Write_Stream_Reply = 0x30  # 00110000
    Write_Stream_Reply_Failure = 0x38  # 0b111000
    Get_Configuration_Options_Command = 0x80  # 10000000
    # 1 sub-operation (same as above using MCOpMasks.Default)
    Get_Configuration_Options_Reply = 0x82    # 10000010
    # ^ special datagram format follows (in later bytes)
    Get_Address_Space_Info_Command = 0x84        # 10000100
    # 2 sub-operations (same as above using MCOpMasks.Default):
    Get_Address_Space_Info_Reply = 0x86          # 10000110
    Get_Address_Space_Info_Reply_Command = 0x87  # 10000111
    Lock_or_Reserve_Command = 0x88  # 10001000
    # 1 sub-operation (same as above using MCOpMasks.Default):
    Lock_or_Reserve_Reply = 0x8A    # 10001010
    Get_Unique_ID_Command = 0x8C  # 10001100
    # 1 sub-operation (same as above using MCOpMasks.Default):
    Get_Unique_ID_Reply = 0x8D    # 10001101
    Unfreeze_Command = 0xA0  # 10100000
    # 1 sub-operation (same as above using MCOpMasks.Default):
    Freeze_Command = 0xA1    # 10100001
    Update_Complete_Command = 0xA8                # 10101000
    # 2 sub-operations (same as above using MCOpMasks.Default):
    Reset_or_Reboot_Command = 0xA9                # 10101001
    Reinitialize_or_Factory_Reset_Command = 0xAA  # 10101010

    @classmethod
    def fromNumber(cls, num: int):
        """Return the MemorySpace member with the given numeric value,
        or None if no match is found.
        """
        assert isinstance(num, int)
        for member in cls:
            if member.value == num:
                return member
        return None


class MCOpBits:
    Failure_Bit = 0x08


class MCOpMasks:
    Default = 0b11111100
    # The following aren't necessary since
    #    they can be broken down with
    #    sub-checks even if Default is used
    #    (See any set with more than one entry
    #    in TWO_BIT_PARAMS):
    # Get_Configuration_Options = 0x11111110
    # Get_Address_Space_Info = 0x11111110


"""
The combined *values* TWO_BIT_PARAMS include all 6-high-bit operation
groups *except* those in OP_FAILURE_BYTES order determines meaning for
lists:
- First ([0]) indicates custom space follows (in later byte)
- Others are standard spaces. For meaning of last 2 bits see
  MemorySpaceIndex Enum (derived from Configuration Description
  Information Standard).
  - Meaningful last 2 bits are *not* applicable if value of dict is a
    *set* (set is used by convention here to indicate no ordered
    meaning)!
  - Ones with *remote* comment (typically with "Command" in the name)
    require a MemoryManager/subclass. Only setup memoryservice instance's
    .memory if your device itself should be remotely configurable (not
    required and not typical for a Configuration Tool, since its purpose
    it to configure other nodes, but for an actual/virtual node, see
    example_node_memory_implementation). Such a Node should set the
    MEMORY_CONFIGURATION_PROTOCOL and other applicable protocols in its
    PIP set (See Node constructor).
    - Each node must have its own MemoryService instance since
      DatagramReceiveMemo does not carry a destination address.
"""
TWO_BIT_PARAMS = {
    # region *lists* (last 2 bits are MemorySpaceIndex.fromNumber param)
    MCOp.Read_Command.value: [0x40, 0x41, 0x42, 0x43],  # remote
    MCOp.Read_Reply.value: [0x50, 0x51, 0x52, 0x53],
    MCOp.Read_Stream_Command.value: [0x60, 0x61, 0x62, 0x63],  # remote
    MCOp.Read_Stream_Reply.value: [0x70, 0x71, 0x72, 0x73],  # TODO
    MCOp.Write_Command.value: [0x00, 0x01, 0x02, 0x03],  # remote
    MCOp.Write_Reply.value: [0x10, 0x11, 0x12, 0x13],
    MCOp.Write_Under_Mask_Command.value: [0x08, 0x09, 0x0A, 0x0B],  # remote
    MCOp.Write_Stream_Command.value: [0x20, 0x21, 0x22, 0x23],
    MCOp.Write_Stream_Reply.value: [0x30, 0x31, 0x32, 0x33],  # TODO
    # endregion

    # region *sets* (no standard meaning to last 2 bits)
    MCOp.Get_Configuration_Options_Command.value: {
        MCOp.Get_Configuration_Options_Command.value,
        MCOp.Get_Configuration_Options_Reply.value,
    },
    MCOp.Get_Address_Space_Info_Command.value: {
        MCOp.Get_Address_Space_Info_Command.value,
        MCOp.Get_Address_Space_Info_Reply.value,
        MCOp.Get_Address_Space_Info_Reply_Command.value,
    },
    MCOp.Lock_or_Reserve_Command.value: {
        MCOp.Lock_or_Reserve_Command.value,
        MCOp.Lock_or_Reserve_Reply.value,
    },
    MCOp.Get_Unique_ID_Command.value: {
        MCOp.Get_Unique_ID_Command.value,
        MCOp.Get_Unique_ID_Reply.value
    },
    MCOp.Unfreeze_Command.value: {0xA1, 0xA0},  # unfreeze, freeze respectively
    MCOp.Update_Complete_Command.value: {  # all match using MCOpMasks.Default
        MCOp.Update_Complete_Command.value,
        MCOp.Reset_or_Reboot_Command.value,
        MCOp.Reinitialize_or_Factory_Reset_Command.value,
    }
    # endregion
}

OP_FAILURE_BYTES = {
    # *lists* (last 2 bits are standard memory space):
    MCOp.Read_Reply.value: [0x58, 0x59, 0x5A, 0x5B],
    MCOp.Read_Stream_Reply.value: [0x78, 0x79, 0x7A, 0x7B],
    MCOp.Write_Reply.value: [0x18, 0x19, 0x1A, 0x1B],
    MCOp.Write_Stream_Reply.value: [0x38, 0x39, 0x3A, 0x3B],
    # *sets* (last 2 bits have no special meaning):
    MCOp.Read_Reply_Failure.value: {
        MCOp.Read_Reply_Failure.value},
    MCOp.Write_Reply_Failure.value: {
        MCOp.Write_Reply_Failure.value},
    MCOp.Read_Stream_Reply_Failure.value: {
        MCOp.Read_Stream_Reply_Failure.value},
    MCOp.Write_Stream_Reply_Failure.value: {
        MCOp.Write_Stream_Reply_Failure.value},
}


class MemoryReadMemo:
    """Memo carries request and reply.

    Args:
        nodeID (NodeID): Remote node id (where to read).
        size (int): Size of the data to be read, typically in bytes.
        space (int): Encoded memory space identifier, where values:
            - 0xFF to 0xFD are special spaces, and only the least significant
              2 bits are relevant.
              - 0xFF is CDI (decodes to 0x03)
            - 0x00 to 0xFC represent standard memory spaces directly.
              - 0xFA is FDI
        address (int): The address in memory where the read operation
            should be performed.
        rejectedReply (Callable[MemoryReadMemo]): Callback function to handle
            rejected read responses.
            The callback will receive this MemoryReadMemo instance.
        dataReply (Callable[MemoryReadMemo]): Callback function to
            handle successful read responses (called after okReply which
            is handled by MemoryService). The callback will receive the
            data read from memory. This is passed as a MemoryReadMemo
            object with the data member set.

    Attributes:
        data(bytearray): The data that was read.
    """
    def __init__(self, nodeID: NodeID, size: int, space: int, address: int,
                 rejectedReply: Callable[['MemoryReadMemo'], None],
                 dataReply: Callable[['MemoryReadMemo'], None]):
        # For args see class docstring.
        self.error = None  # type: str|None
        self.errorCode = None  # type: int|None
        self.nodeID = nodeID
        assert isinstance(size, int)
        self.size = size
        if isinstance(space, MemorySpace):
            space = space.value
        assert isinstance(space, int)
        self.space = space
        assert isinstance(address, int)
        self.address = address
        self.rejectedReply = rejectedReply
        self.dataReply = dataReply
        # for convenience, data can be added or updated after creation of the
        # memo
        self.data = bytearray()
        assertMemoOK(self)


class MemoryWriteMemo:
    """A memory write request within an OpenLCB network.
    Args:
        nodeID (NodeID): Remote node id (where to write).
        okReply (Callable): Callback function to handle successful write
            responses. The callback receives this MemoryWriteMemo instance.
        rejectedReply (Callable): Callback function to handle rejected
            write responses. The callback receives this MemoryWriteMemo
            instance.
        size (int): Size of the data to be written in bytes.
        space (int): Encoded memory space identifier, where values:
            - 0xFF to 0xFD are special spaces, and only the least significant
              2 bits are relevant.
            - 0x00 to 0xFC represent standard memory spaces directly.
        address (int): The address in memory where the data should be
            written.
        data (bytes): The actual data to be written to the specified
            memory address.
    """

    def __init__(self, nodeID: NodeID,
                 okReply: Callable[['MemoryWriteMemo'], None],
                 rejectedReply: Callable[['MemoryWriteMemo'], None],
                 size: int, space: int, address: int, data: bytearray):
        # For args see class docstring.
        self.error = None  # type: str|None
        self.errorCode = None  # type: int|None
        self.nodeID = nodeID
        self.okReply = okReply
        self.rejectedReply = rejectedReply
        self.size = size  # max 64 bytes
        self.space = space
        self.address = address
        self.data = data
        assertMemoOK(self)


def assertMemoOK(memo: Union[MemoryReadMemo, MemoryWriteMemo]):
    assert isinstance(memo.space, int), \
        f"Expected int or MemorySpace.value, got space={emit_cast(memo.space)}"
    assert isinstance(memo.size, int), \
        f"Expected int, got size={emit_cast(memo.size)}"
    # TODO: > 64 is only ok for a length request (?)
    # assert memo.size <= 64, \
    #     f"Expected <= 64, got size={memo.size}"
    assert isinstance(memo.address, int), \
        f"Expected int, got address={emit_cast(memo.address)}"
    assert len(memo.data) <= 64
    assert isinstance(memo.data, (bytes, bytearray)), \
        f"Expected bytearray, got data={emit_cast(memo.data)}"


def parseReplyDatagram(memo: Union[MemoryReadMemo, MemoryWriteMemo],
                       dmemo: Union[DatagramReceiveMemo, DatagramSendMemo]):
    """Parse dmemo and set errorCode and/or error attributes of memo"""
    if not dmemo.data or dmemo.data[0] != 0x20:
        logger.warning(
            "Datagram type is not memory configuration (0x20)"
            f" it is {hex(dmemo.data[0])}")
        return
    if len(dmemo.data) < 2:
        logger.warning(
            "Datagram is truncated to 1 byte:"
            f" it is {hex(dmemo.data[0])}")
        return
    mcHeader = MemoryConfigurationHeader.fromMC2ndByte(
        dmemo.data[1],
        # space=memo.space,
    )
    offset = 6
    error = None
    if mcHeader.spaceIndex in (MemorySpaceIndex.Custom,
                               MemorySpaceIndex.Uninitialized):
        # mcHeader.customSpace = memo.space
        mcHeader.customSpace = dmemo.data[6]
        offset = 7
    else:
        assert mcHeader.customSpace is None, \
            "fromMC2ndByte should not set customSpace in this case"
    memo.error = None
    memo.errorCode = None
    logger.info(f"reply datagram: {mcHeader.spaceIndex}"
                f" customSpace={mcHeader.customSpace}")
    if (dmemo.data[1] & 0x08 == 0):
        # ok reply
        return
    else:
        pass
        # 0x08 (0b00001000) is error bit
        # mode = None
        # for k, values in OP_FAILURE_BYTES.items():
        #     if dmemo.data[1] in values:
        #         mode = k
        #         break
        # if mode is not None:
        #     error = f"No {mode} error code."
        # else:
        #     error = f"No error code for unknown mode {hex(dmemo.data[1])}."
    code_idx = offset

    if len(dmemo.data) < code_idx + 2:
        memo.error = error
        if len(dmemo.data) == code_idx + 1:
            memo.error = (
                f"malformed error code {hex(dmemo.data[code_idx])}"
                " (expected 2 bytes)")
        memo.errorCode = dmemo.data[code_idx]
        return
    error = None
    # Decode big-endian number:
    memo.errorCode = (dmemo.data[code_idx] << 8) + dmemo.data[code_idx+1]
    message_idx = code_idx + 2
    if len(dmemo.data) > message_idx:
        error_bytes = Convert.getBeforeNull(dmemo.data, message_idx)
        error = error_bytes.decode("utf-8")
        if len(error) == 1:
            error += f" ({hex(dmemo.data[message_idx])})"
        elif len(error) == 0 and (len(dmemo.data) - message_idx > 0):
            error += f" ({list(dmemo.data[message_idx:])})"
    else:
        error = f"(2nd byte = {hex(dmemo.data[1])})"
    error += f" (spaceIndex={mcHeader.spaceIndex})"
    if mcHeader.spaceIndex is mcHeader.customSpace:
        if mcHeader.customSpace is not None:
            if mcHeader.customSpace != dmemo.data[6]:
                error += f" (mcHeader.customSpace={hex(mcHeader.customSpace)} != space={hex(dmemo.data[6])} !)"  # noqa: E501
            else:
                error += f" (mcHeader.customSpace={hex(mcHeader.customSpace)})"
        else:
            error += f" (space={hex(dmemo.data[6])} mcHeader.customSpace=None!)"  # noqa: E501
    memo.error = error


class MemoryService:
    """Manage memory read and write requests
    (64 bytes at a time).

    Args:
        service (DatagramService): See DatagramService.

    Attributes:
        memory (Union[MemoryManager, LocalNode]): The storage
            (all segments specific to this node) where other nodes can
            read and write memory. Since a datagram doesn't have a
            destination, there must be a MemoryService for each local
            node (the local Configuration Tool or node and any virtual
            nodes. Though typically a Configuration Tool isn't itself
            configured remotely, that is technically possible, and
            more typical in cases where it generates virtual nodes).
    """

    def __init__(self, service: DatagramService):
        self.service: DatagramService = service
        self.readMemos: List[MemoryReadMemo] = []
        self.writeMemos: List[MemoryWriteMemo] = []
        self.spaceLengthCallback: Union[Callable[[int], None], None] = None

        # register to DatagramService to hear arriving datagrams
        self.service.registerDatagramReceivedListener(
            self.datagramReceivedListener
        )
        self.memory = MemoryManager()  # type: MemoryManager|LocalNode

    def requestMemoryRead(self, memo, stream: bool = False):
        # type: (MemoryReadMemo, Optional[bool]) -> None
        '''Request a read operation start.

        - If okReply in the memo is triggered, it will be followed by a
          dataReply.

        - A rejectedReply will not be followed by a dataReply.

        Args:
            memo (MemoryReadMemo): Request to enqueue.
        '''
        assert isinstance(stream, bool)
        # preserve the request
        self.readMemos.append(memo)

        if len(self.readMemos) == 1:
            self.requestMemoryReadNext(memo, stream=stream)

    def requestMemoryReadNext(self, memo, stream: bool = False):
        # type: (MemoryReadMemo, Optional[bool]) -> None
        """send the read request

        Args:
            memo (MemoryReadMemo): Request to send.
        """
        assert isinstance(stream, bool)
        mcHeader = MemoryConfigurationHeader(memo.space)
        assert mcHeader.spaceIndex is not None
        spaceFlag = (0x60 if stream else 0x40) | mcHeader.spaceIndex.value
        # NOTE: Why was there commented: | 0xFC (0b11111100) if not stream?
        addr2 = ((memo.address >> 24) & 0xFF)
        addr3 = ((memo.address >> 16) & 0xFF)
        addr4 = ((memo.address >> 8) & 0xFF)
        addr5 = (memo.address & 0xFF)
        data = bytearray([
            DatagramService.ProtocolID.MemoryOperation.value, spaceFlag,
            addr2, addr3, addr4, addr5])
        # NOTE: list[int] is ok for bytearray extend (`+` requires cast)
        if mcHeader.customSpace is not None:
            assert memo.space <= 0xFF, f"Space {memo.space} out of byte range"
            data.extend([(memo.space & 0xFF)])
        data.extend([memo.size])
        logger.debug(
            "[requestMemoryReadNext] creating DatagramSendMemo"
            f" to destID={memo.nodeID} with data={list(data)}")
        dgSendMemo = DatagramSendMemo(memo.nodeID, data,
                                      self.receivedOkReplyToWrite)
        self.service.sendDatagram(dgSendMemo)

    def receivedOkReplyToWrite(self, memo: Union[DatagramSendMemo, None]):
        '''Wait for following response to be returned via listener.
        This is normal.
        '''
        pass

    def datagramReceivedListener(self, dmemo: DatagramReceiveMemo) -> bool:
        '''Process a datagram.

        Sends the positive reply and returns true if this is from our service.
        '''
        # node received a datagram, is it our service?
        if self.service.datagramType(dmemo.data) \
                != DatagramService.ProtocolID.MemoryOperation :
            return False
        # datagram must has a command value
        if len(dmemo.data) < 2:
            logger.error("Memory service datagram too short: {}"
                         .format(dmemo.data.count))
            # TODO: ^ more necessary to show same output as Swift? Formerly:
            #   " \(dmemo.data.count, privacy: .public)")
            self.service.negativeReplyToDatagram(dmemo, 0x1041)
            return True  # error, but for our service; sent negative reply
        # Acknowledge the datagram
        self.service.positiveReplyToDatagram(dmemo, 0x0000)
        mcOp = MCOp.fromNumber(dmemo.data[1] & MCOpMasks.Default)
        # decode if read, write or some other reply
        if dmemo.data[1] in (0x50, 0x51, 0x52, 0x53, 0x58, 0x59, 0x5A, 0x5B):
            # assert mcOp is MCOp.Read_Reply, \
            #     "self-test failed (bad constant(s))"
            # assert (dmemo.data[1] in TWO_BIT_PARAMS[mcOp.value]
            #         or dmemo.data[1] in OP_FAILURE_BYTES[mcOp.value]), \
            #     "self-test failed (bad constant(s))"
            # MCOp.Read_Reply
            # read or read-error reply

            # return data to requestor: first find matching memory read
            # memo, then reply
            for index in range(0, len(self.readMemos)):
                if self.readMemos[index].nodeID == dmemo.srcID:
                    tMemoryMemo = self.readMemos[index]  # type: MemoryReadMemo
                    del self.readMemos[index]
                    # decode type of operation, hence offset for start of
                    # data
                    offset = 6
                    if dmemo.data[1] == 0x50 or dmemo.data[1] == 0x58:
                        offset = 7

                    # are there any additional requests queued to send?
                    if len(self.readMemos) > 0:
                        self.requestMemoryReadNext(self.readMemos[0])

                    parseReplyDatagram(tMemoryMemo, dmemo)
                    # fill data for call-back to requestor
                    if len(dmemo.data) > offset:
                        tMemoryMemo.data = dmemo.data[offset:]
                        logger.debug(
                            f"[datagramReceivedListener] got read reply"
                            f" data={list(tMemoryMemo.data)} offset={offset}"
                            f", requested @{tMemoryMemo.address}")

                    # check for read or read error reply
                    if (dmemo.data[1] & 0x08 == 0):
                        tMemoryMemo.dataReply(tMemoryMemo)
                    else:
                        tMemoryMemo.rejectedReply(tMemoryMemo)
                    break
        elif dmemo.data[1] in (0x10, 0x11, 0x12, 0x13, 0x18, 0x19, 0x1A, 0x1B):
            # assert mcOp is MCOp.Write_Reply, \
            #     (f"self-test failed (bad constant(s));"
            #      f" got op {mcOp} for sub-op {hex(dmemo.data[1])}")
            # write reply good, bad

            # return data to requestor: first find matching memory write
            # memo, then reply
            for index in range(0, len(self.writeMemos)):
                if self.writeMemos[index].nodeID == dmemo.srcID:
                    writeMemo = self.writeMemos[index]  # type: MemoryWriteMemo
                    del self.writeMemos[index]
                    parseReplyDatagram(writeMemo, dmemo)
                    if dmemo.data[1] & 0x08 == 0 :
                        writeMemo.okReply(writeMemo)
                    else:
                        writeMemo.rejectedReply(writeMemo)
                    break
        elif dmemo.data[1] == MCOp.Get_Address_Space_Info_Command.value:
            # 0x84 (A node sent us a command requesting space info)
            # assert mcOp is MCOp.Get_Address_Space_Info_Command, \
            #     "self-test failed (bad constant(s))"
            logger.info("[MemoryService datagramReceivedListener]"
                        " Get_Address_Space_Info_Command")
            space = dmemo.data[2]
            last = self.memory.getLast(space)
            if last is not None:
                logger.info("Found populated segment...")
                first = self.memory.getFirst(space)
                assert isinstance(first, int)
                assert last - first >= 0, \
                    (f"{type(self.memory).__name__} incorrectly implemented:"
                     " first>last")
                ReadOnly = 0b10000000
                HasLowestAddress = 0b01000000
                highestAddrBytes = struct.pack(">I", last)
                assert len(highestAddrBytes) == 4
                # TODO: ^ Memory Configuration Standard doesn't say
                #   unsigned/signed, so assuming unsigned for
                #   highestAddrBytes (and lowestAddrBytes below)
                replyData = bytearray([
                    DatagramService.ProtocolID.MemoryOperation.value,
                    0x87,  # If 0x86, bytes after first three can be omitted.
                    space,
                ])
                if replyData[1] == 0x87:
                    replyData += highestAddrBytes  # bytes 3-6 (0 indexed)
                    replyData.append(0x00)  # flags (set below)
                    if self.memory.isReadOnly(space):
                        replyData[-1] |= ReadOnly
                    if first != 0:
                        replyData[-1] |= HasLowestAddress
                        lowestAddrBytes = struct.pack(">I", first)
                        assert len(lowestAddrBytes) == 4
                        replyData += lowestAddrBytes
                    description = self.memory.getDescription(space)
                    if description:
                        descBytes = bytearray(description.encode())
                    else:
                        descBytes = bytearray()
                    descBytes.append(0)
                    # FIXME: is null-terminator is required if no
                    #   description (See
                    #   https://github.com/openlcb/documents/issues/190)?
                    replyData += descBytes
                    # FIXME: Need to send Datagram Received OK datagram 1st?
                    spaceInfoReplyMemo = DatagramSendMemo(
                        dmemo.srcID,
                        replyData
                    )
                    self.service.sendDatagram(spaceInfoReplyMemo)
                    logger.info("- added extended info")
                else:
                    logger.info("- skipping simple reply")
            else:
                error = (f"- rejected (No last address for space"
                         f" {hex(space)}): {Convert.toHex(dmemo.data)}")
                logger.info(error)
                if isinstance(self.memory, MemoryManager):
                    if space == 0xFF:
                        logger.warning(
                            "MemoryManager does not have CDI by default."
                            " Use its subclass LocalNode to load CDI XML.")
                errorCode = 1
                address = 0
                # FIXME: Is this the right error reply? If not make memo here
                failedMemo = MemoryService.failedMemo(
                    MCOp.Read_Reply_Failure, dmemo.srcID, address, space,
                    errorCode, error)
                self.service.sendDatagram(failedMemo)
                return True  # handled (early, in error case)

        elif dmemo.data[1] in (0x86, 0x87):  # Address Space Information Reply
            # assert mcOp is MCOp.Get_Address_Space_Info_Command, \
            #     "self-test failed (bad constant(s))"
            # ^ same first 6 bits as Get_Address_Space_Info_Command,
            #   but in this case actually a reply to a command.

            if self.spaceLengthCallback is None:
                logger.error("Address Space Information Reply"
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
        elif mcOp in (MCOp.Read_Command, MCOp.Write_Command):
            # See OpenLCB Memory Configuration Standard, section 4.4 & 4.8
            mcHeader = MemoryConfigurationHeader.fromMC2ndByte(dmemo.data[1])
            addressBytes = dmemo.data[2:6]
            address = struct.unpack(">I", addressBytes)[0]
            # ^ [0] since always returns list even when reading 1 value.
            # ^ capital assumes unsigned, "I" assumes 32-bit (4 bytes)
            spaceIndex = dmemo.data[1] & 0b00000011
            offset = 0
            space = None
            if mcHeader.spaceIsCustom():
                assert spaceIndex == 0
                space = dmemo.data[6]
                offset = 1
            replyHighBits = MCOp.Read_Reply.value
            if mcOp is MCOp.Write_Command:
                replyHighBits = MCOp.Write_Reply.value
            replyBytes = bytearray([0x20, replyHighBits])
            # ^ byte1 (2nd) changed to error below if applicable
            assert isinstance(spaceIndex, int), \
                (f"Logic missing, spaceIndex should be number here,"
                 f" got {emit_cast(spaceIndex)}")
            assert isinstance(address, int)
            replyBytes += addressBytes
            if mcHeader.spaceIsCustom():
                assert space is not None
                replyBytes.append(space)
                assert len(replyBytes) == 7, "space goes in index [6]"
            else:
                space = MemorySpace.fromIndex(MemorySpaceIndex(spaceIndex))
                assert space is not None
                space = space.value
                spaceIndex = (space & 0b00000011)
                assert space is not None
                replyBytes[1] = \
                    replyBytes[1] | spaceIndex
                assert len(replyBytes) == 6, "should not have space in [6]"
            assert space is not None, \
                f"space not computed from datagram: {dmemo.data}"
            if mcOp is MCOp.Read_Command:
                # assert dmemo.data[1] \
                #         in TWO_BIT_PARAMS[MCOp.Read_Command.value],\
                #     "self-test failed (bad constant(s))"
                size = dmemo.data[6+offset]  # requested read count
                size = size & 0b01111111  # upper bit is reserved

                payload = None
                try:
                    segment = self.memory.getSegment(space)
                    if segment is None:
                        raise KeyError(f"space {space} is not valid")
                    if address >= segment.size():
                        raise IndexError(
                            f"address {address} past end of {hex(space)}")
                    payload = self.memory.getSlice(space, address, size,
                                                   force=True)
                    # ^ force=True because reading past end is normal
                    #   (pad with zeroes to indicate end)
                except (IndexError, KeyError) as ex:
                    # address out of range (See Segment's getSlice)
                    replyBytes[1] = MCOp.Read_Reply_Failure.value
                    message = None
                    if isinstance(ex, KeyError):
                        message = f"space {space} not valid"
                    elif isinstance(ex, IndexError):
                        if space is not None:
                            message = (f"address {hex(address)} not valid"
                                       f" in space {hex(space)}")
                        else:
                            raise NotImplementedError(
                                f"space not computed from datagram:"
                                f" {dmemo.data}")
                    errorCode = 1
                    failedMemo = MemoryService.failedMemo(mcOp, dmemo.srcID,
                                                          address,
                                                          space, errorCode,
                                                          message)
                    self.service.sendDatagram(failedMemo)
                    return True  # handled (early, in error case)
                assert payload is not None, \
                    ("getSlice failed to raise IndexError or KeyError"
                     " on invalid request (expected bytes, got None)")
                assert len(payload) <= 64
                replyBytes += payload
                requestedMemoryMemo = DatagramSendMemo(
                    dmemo.srcID,
                    replyBytes
                )
                # FIXME: Must we manually send Datagram Received OK first?
                self.service.sendDatagram(requestedMemoryMemo)
                return True  # handled (early in this case)
            elif mcOp is MCOp.Write_Command:
                try:
                    segment = self.memory.getSegment(space)
                    if segment is None:
                        raise KeyError(f"space {space} is not valid")
                    if address >= segment.size():
                        raise IndexError(
                            f"address {address} past end of {hex(space)}")
                    receivedPayload = dmemo.data[6+offset:]
                    if len(receivedPayload) < 1:
                        logger.warning(f"Got {mcOp} with payload size of 0")
                    self.memory.setSlice(space, address, receivedPayload)
                    # TODO: force=true is ok for read, not sure if ok for write
                except (IndexError, KeyError) as ex:
                    # address out of range (See Segment's getSlice)
                    replyBytes[1] = MCOp.Read_Reply_Failure.value
                    message = None
                    if isinstance(ex, KeyError):
                        message = f"space {space} not valid"
                    elif isinstance(ex, IndexError):
                        if space is not None:
                            message = (f"address {hex(address)} not valid"
                                       f" in space {hex(space)}")
                        else:
                            raise NotImplementedError(
                                f"space not computed from datagram:"
                                f" {dmemo.data}")
                    errorCode = 1
                    failedMemo = MemoryService.failedMemo(mcOp, dmemo.srcID,
                                                          address,
                                                          space, errorCode,
                                                          message)
                    self.service.sendDatagram(failedMemo)
                    return True  # handled (early, in error case)
        else:
            logger.error("Did not expect reply of type 0x{:02X}"
                         .format(dmemo.data[1]))
        return True

    @staticmethod
    def failedMemo(mcOp: MCOp, srcID: NodeID, address: int, space: int,
                   errorCode: int, message) -> DatagramSendMemo:
        assert isinstance(mcOp, MCOp)
        assert isinstance(srcID, NodeID)
        assert isinstance(address, int)
        if isinstance(space, MemorySpaceIndex):
            space = space.value
        elif isinstance(space, MemorySpace):
            space = space.value
        assert isinstance(space, int)
        assert isinstance(errorCode, int)
        space = space & 0b00000011
        replyBytes = bytearray([0x20, mcOp.value | space])
        assert errorCode <= 65535
        errorBytes = struct.pack(">H", errorCode)
        # FIXME: ^ Standard doesn't specify signed/unsigned
        replyBytes += errorBytes  # 2 required bytes

        messageBytes = None
        if message is not None:
            messageBytes = bytearray(message.encode("utf-8"))
            messageBytes.append(0x00)  # null terminator
            replyBytes += messageBytes
        return DatagramSendMemo(
            srcID,
            replyBytes
        )

    def requestMemoryWrite(self, memo: MemoryWriteMemo, stream: bool = False):
        # type: (MemoryWriteMemo, Optional[bool]) -> None
        """Request memory write.

        Args:
            memo (MemoryWriteMemo): information to send
        """
        assert isinstance(stream, bool)
        # preserve the request
        self.writeMemos.append(memo)
        # create & send a write datagram
        hasByte6 = False  # if custom space is defined in byte 6
        header = MemoryConfigurationHeader(memo.space)
        spaceFlag = (0x20 if stream else 0) | header.spaceIndex.value
        addr2 = ((memo.address >> 24) & 0xFF)
        addr3 = ((memo.address >> 16) & 0xFF)
        addr4 = ((memo.address >> 8) & 0xFF)
        addr5 = (memo.address & 0xFF)
        data = bytearray([
            DatagramService.ProtocolID.MemoryOperation.value, spaceFlag,
            addr2, addr3, addr4, addr5
        ])
        if hasByte6:
            assert memo.space <= 0xFF, f"Space {memo.space} out of byte range"
            data.extend([(memo.space & 0xFF)])
        data.extend(memo.data)
        dgWriteMemo = DatagramSendMemo(memo.nodeID, data)
        self.service.sendDatagram(dgWriteMemo)

    def requestSpaceLength(self, space: int, nodeID: NodeID,
                           callback: Callable[[int], None]):
        '''Request the length of a specific memory space from a remote node.

        Args:
            space (int): Encoded memory space identifier. This can be a
                value within a specific range, as defined in the
                `serializeSpace` method.
            nodeID (NodeID): ID of remote node from which the memory
                space length is requested.
            callback (Callable): Callback function that will receive the
                response. The callback will receive an integer address
                as a parameter, representing the address of the
                requested memory space or -1 if not present.

        Returns:
            None
        '''
        if self.spaceLengthCallback is not None:
            logger.error("Overlapping calls to requestSpaceLength")
            return
        self.spaceLengthCallback = callback
        # send request
        dgReqMemo = DatagramSendMemo(
            nodeID,
            bytearray([
                DatagramService.ProtocolID.MemoryOperation.value,
                0x84,
                space
            ])
        )
        self.service.sendDatagram(dgReqMemo)
