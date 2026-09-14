'''
Demo of using the memory service to read the CDI from memory, then an
example of parsing

Usage:
python3 example_memory_transfer.py [host|host:port]

Options:
host|host:port            (optional) Set the address (or using a colon,
                          the address and port). Defaults to a hard-coded test
                          address and port.
'''
# region same code as other examples
import copy
import sys
import time
from typing import Union
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader  # for static type hints, autocomplete in this case

from logging import getLogger

from examples_settings import Settings  # do 1st to fix path if no pip install
from openlcb import precise_sleep
from openlcb.dataprocessor import DataFormat
from openlcb.dataprocessormemo import DataProcessorMemo
from openlcb.memoryreadjob import MemoryReadJob
from openlcb.convert import Convert
from openlcb.memoryspace import MemorySpace
from openlcb.xmldataprocessor import attrs_to_dict
from openlcb.tcplink.tcpsocket import TcpSocket
settings = Settings()

if __name__ == "__main__":
    settings.load_cli_args(docstring=__doc__)
    logger = getLogger(__file__)
else:
    logger = getLogger(__name__)
# endregion same code as other examples

from openlcb.canbus.canphysicallayergridconnect import (  # noqa:E402
    CanPhysicalLayerGridConnect,
)
from openlcb.canbus.canlink import CanLink  # noqa:E402
from openlcb.nodeid import NodeID  # noqa:E402
from openlcb.datagramservice import (  # noqa:E402
    DatagramService,
)
from openlcb.memoryservice import (  # noqa:E402
    MemoryReadMemo,
    MemoryService,
)

# specify connection information
# region moved to settings
# host = "192.168.16.212"
# port = 12021
# localNodeID = "05.01.01.01.03.01"
# # farNodeID = "09.00.99.03.00.35"
# farNodeID = "02.01.57.00.04.9C"
# endregion moved to settings

sock = TcpSocket()
# s.settimeout(30)
sock.connect(settings['host'], settings['port'])


# print("RR, SR are raw socket interface receive and send;"
#      " RL, SL are link interface; RM, SM are message interface")


# def sendToSocket(frame: CanFrame):
#     string = frame.encodeAsString()
#     # print("      SR: {}".format(string.strip()))
#     sock.sendString(string)
#     physicalLayer.onFrameSent(frame)


def printFrame(frame):
    # print("   RL: {}".format(frame))
    pass


def printMessage(message):
    # print("RM: {} from {}".format(message, message.source))
    pass


def printDatagram(memo):
    """A call-back for when datagrams received

    Args:
        DatagramReceiveMemo: The datagram object

    Returns:
        bool: Always False (True would mean we sent a reply to the datagram,
            but let the MemoryService do that).
    """
    # print("Datagram receive call back: {}".format(memo.data))
    return False


physicalLayer = CanPhysicalLayerGridConnect()
physicalLayer.registerFrameReceivedListener(printFrame)

canLink = CanLink(physicalLayer, NodeID(settings['localNodeID']))
canLink.registerMessageReceivedListener(printMessage)

datagramService = DatagramService(canLink)
canLink.registerMessageReceivedListener(datagramService.process)

datagramService.registerDatagramReceivedListener(printDatagram)

memoryService = MemoryService(datagramService)

#######################
# The XML parsing section.
#
# This creates a handler object that just prints
# information as it's presented.
#
# Since `characters` can be called multiple times
# in a row, we buffer up the characters until the `endElement`
# call is invoked to indicate the text is complete


class MyHandler(xml.sax.handler.ContentHandler):
    """XML SAX callbacks in a handler object

    Attributes:
        _chunks (list[str]): Collects chunks of data.
            This is implementation-specific, and not
            required if streaming (parser.feed).
        _tmp_address (int|None): For sanity check, not actual address.
            See replicatedTree docstring.
    """

    def __init__(self):
        self._chunks = []
        self.stack = []
        self.cursorCol = 0
        self._tmp_space = None  # type: int|None
        self._tmp_address = None  # type: int|None

    def startElement(self, name: str, attrs: xml.sax.xmlreader.AttributesImpl):
        """See xml.sax.handler.ContentHandler documentation."""
        self.stack.append(name)
        if self.cursorCol != 0:
            self.print()
        self.write(name)
        if attrs is not None and attrs:
            self.print(" {}".format(attrs_to_dict(attrs)))

    def endElement(self, name: str):
        """See xml.sax.handler.ContentHandler documentation."""
        content = self._flushCharBuffer().strip()
        if self.cursorCol != 0:
            self.print()
        if content:
            self.print('/{} "{}"'.format(name, content))
        else:
            self.print('/{}'.format(name))
        self.stack.pop()
        # self.print("/", name)
        pass

    def write(self, *args, **kwargs):
        args = list(args)
        if self.cursorCol == 0:
            tab = len(self.stack)*"  "
            self.cursorCol += len(tab)
            args.insert(0, tab)  # prepend indent
        for arg in args:
            sys.stdout.write(arg)
            self.cursorCol += len(arg)
            sys.stdout.flush()

    def print(self, *args, **kwargs):
        if self.cursorCol == 0:  # No indent yet, so use write.
            self.write(*args, **kwargs)
            print()
        else:
            print(*args, **kwargs)
        self.cursorCol = 0

    def _flushCharBuffer(self):
        """Decode the buffer, clear it, and return all content.
        See xml.sax.handler.ContentHandler documentation.

        Returns:
            str: The content of the bytes buffer decoded as utf-8.
        """
        s = ''.join(self._chunks)
        self._chunks.clear()
        return s

    def characters(self, content: str):
        """Received characters handler.
        See xml.sax.handler.ContentHandler documentation.

        Args:
            data (Union[bytearray, bytes, list[int]]): any
              data (any type accepted by bytearray extend).
        """
        if not isinstance(content, str):
            raise TypeError("Expected str, got {}"
                            .format(type(content).__name__))
        self._chunks.append(content)


handler = MyHandler()

#######################

# have the socket layer report up to bring the link layer up and get an alias
print("      QUEUE frames : link up...")
physicalLayer.physicalLayerUp()
print("      QUEUED frames : link up...waiting...")
while canLink.pollState() != CanLink.State.Permitted:
    # provides incoming data to physicalLayer & sends queued:
    physicalLayer.receiveAll(sock, verbose=True)
    physicalLayer.sendAll(sock)

    if canLink.getState() == CanLink.State.WaitForAliases:
        # physicalLayer.receiveAll(sock, verbose=True)
        physicalLayer.sendAll(sock)
        # ^ prevent assertion error below, proceed to send.
    if canLink.pollState() == CanLink.State.Permitted:
        break
    assert canLink.getWaitForAliasResponseStart() is not None, \
        ("openlcb didn't send the 7,6,5,4 CID frames (state={})"
         .format(canLink.getState()))
    precise_sleep(.02)
print("      SENT frames : link up")


job = MemoryReadJob(memoryService)


def statusCallback(memo: DataProcessorMemo):
    if memo.status:
        print(memo.status)


farNodeID = NodeID(settings['farNodeID'])

time.sleep(.21)
# ^ 200ms: See section 6.2.1 of CAN Frame Transfer Standard
#   (CanLink.State.Permitted will only occur after that, but waiting
#   now will reduce output & delays below in this example).
while canLink.getState() != CanLink.State.Permitted:
    print("Waiting for connection sequence to complete...")
    # This delay could be .2 (per alias collision), but longer to
    #   reduce console messages:
    time.sleep(.5)

print(f"CanLink state={canLink.getState()}")

waited = 0
delaySec = 1
while farNodeID not in canLink.nodeIdToAlias:
    # canLink.pollState()
    physicalLayer.receiveAll(sock)
    physicalLayer.sendAll(sock)
    time.sleep(delaySec)
    waited += delaySec
    print(f"Connected nodes: {canLink.nodeIdToAlias}")
    print(f"Waiting for {farNodeID} ({waited}s)...")

job.readMemory(canLink, farNodeID, MemorySpace.CDI,
               handler=handler,
               callback=statusCallback)

previous_nodes = copy.deepcopy(canLink.nodeIdToAlias)
# process resulting activity
print()
print("This example will exit on failure or complete data.")
while not job.completeData and not job.failed:
    # In this example, requests are initiate by the
    #   memoryRead thread, and receiveAll actually
    #   receives the data from the requested memory space (CDI in this
    #   case) and offset (incremental position in the file/data,
    #   incremented by this example's memoryReadSuccess handler).
    count = 0
    count += physicalLayer.receiveAll(sock)
    count += physicalLayer.sendAll(sock)
    if canLink.nodeIdToAlias != previous_nodes:
        print("nodeIdToAlias updated: {}".format(canLink.nodeIdToAlias))
    if count < 1:
        precise_sleep(.01)
    # else skip sleep to avoid latency (port already delayed)
    if canLink.nodeIdToAlias != previous_nodes:
        previous_nodes = copy.deepcopy(canLink.nodeIdToAlias)

physicalLayer.physicalLayerDown()

if job.failed:
    print("Read complete (FAILED)")
else:
    print("Read complete (OK)")
