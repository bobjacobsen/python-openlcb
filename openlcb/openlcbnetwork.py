
"""
CDI Frame

A reusable superclass for Configuration Description Information
(CDI) processing and editing.

This file is part of the python-openlcb project
(<https://github.com/bobjacobsen/python-openlcb>).

Contributors: Poikilos, Bob Jacobsen (code from example_cdi_access)
"""
import sys
import threading
from timeit import default_timer
from typing import Callable, Union

from logging import getLogger

from openlcb import (
    formatted_ex,
    precise_sleep,
)
from openlcb.canbus.canphysicallayergridconnect import (
    CanPhysicalLayerGridConnect,
)
from openlcb.canbus.canlink import CanLink
from openlcb.cdimemo import CDIMemo
from openlcb.datagramservice import DatagramReceiveMemo, DatagramService
from openlcb.dataprocessor import DataFormat
from openlcb.dataprocessormemo import DataProcessorMemo
from openlcb.memoryservice import MemoryReadMemo, MemoryService
from openlcb.memoryspace import MemorySpace
from openlcb.message import Message
from openlcb.xmldataprocessor import XMLDataProcessor
from openlcb.mti import MTI
from openlcb.nodeid import NodeID
from openlcb.portinterface import PortInterface

if __name__ == "__main__":
    logger = getLogger(__file__)
else:
    logger = getLogger(__name__)


class OpenLCBNetwork:
    """OpenLCB network manager.

    The lower-level classes can also be used, but this is class is valid
    for reference and practical use. CanLink manages network states, but
    this class manages the network objects themselves including CanLink.

    Attributes:
        _dataProcessor (XMLDataProcessor): The handler for the current
            type of data (type is defined by _dataProcessor.space which
            is a MemorySpace)
    """
    def __init__(self, localNodeID: Union[str, bytearray, int, NodeID]):
        self._onConnect: Union[Callable[[DataProcessorMemo], None], None] = None
        self._port: PortInterface = None
        self.physicalLayer: CanPhysicalLayerGridConnect = None
        self.canLink: CanLink = None

        self._fireStatus("CanPhysicalLayerGridConnect...")
        self.physicalLayer = CanPhysicalLayerGridConnect()
        self._fireStatus("CanLink...")
        self.canLink = CanLink(self.physicalLayer, NodeID(localNodeID))
        # ^ CanLink constructor sets _physicalLayer's onFrameReceived
        #   and onFrameSent to handlers in _canLink.
        self._fireStatus("CanLink...registerMessageReceivedListener...")
        self.canLink.registerMessageReceivedListener(self._handleMessage)
        # NOTE: Incoming data (Memo) is handled by _memoryReadSuccess
        #   and _memoryReadFail.
        #   - These are set when constructing the MemoryReadMemo which
        #     is provided to openlcb's requestMemoryRead method.

        # region connect
        self._datagramService: DatagramService = None
        self._memoryService: MemoryService = None
        # endregion connect

        self._connectingStart: float = None

        self._fireStatus("DatagramService...")
        self._datagramService = DatagramService(self.canLink)
        self.canLink.registerMessageReceivedListener(
            self._datagramService.process
        )

        self._datagramService.registerDatagramReceivedListener(
            self._printDatagram
        )

        self._fireStatus("MemoryService...")
        self._memoryService = MemoryService(self._datagramService)
        self._dataProcessor: XMLDataProcessor = None

    @property
    def memoryService(self):
        return self._memoryService

    def setConnectHandler(self, handler: Callable[[CDIMemo], None]):
        """Deprecated in favor of a Message handler,
        Since it is the socket loop's responsibility to call
        physicalLayerUp and physicalLayerDown, and those each trigger a
        Message (See Link_Layer_Up and Link_Layer_Down in _handleMessage
        in examples_gui.py)
        """
        self._onConnect = handler

    def startListening(self, connected_port):
        if self._port is not None:
            logger.warning(
                "[startListening] A previous _port will be discarded.")
        self._port = connected_port

        self._fireStatus("listen...")

        self.listen()

    def listen(self):
        self._listenThread = threading.Thread(
            target=self._listen,
            daemon=True,  # True to terminate on program exit
        )
        print("[listen] Starting port receive loop...")
        self._listenThread.start()

    def _receive(self) -> bytearray:
        """Receive data from the port.
        Override this if serial/other subclass not using TCP
        (or better yet, make all ports including TcpSocket inherit from
        a standard port interface)
        Returns:
            bytearray: Data, or None if no data (BlockingIOError is
                handled by PortInterface, *not* passed up the
                callstack).
        """
        return self._port.receive()

    def _startMemoryRead(self, farNodeID: Union[NodeID, int, str, bytearray]):
        """Create and send a read datagram.
        This is a read of 64 bytes from the start of CDI space.
        We will fire it on a separate thread to give time for other nodes to
        reply to AME.

        Before calling this, ensure connect returns (or that you
        manually do the 200 ms wait it has built in). That ensures nodes
        announce, otherwise sendMessage (triggered by requestMemoryRead)
        will have a KeyError when trying to use the farNodeID.

        Requirements:
        - self._dataProcessor must be set. In practice, MemoryReadMemo
          objects are a sequential chain, so OpenLCBNetwork uses
          self._dataProcessor determine that each MemoryReadMemo space in
          the chain is consistent as well as know what is expected in a
          reply (Message).
        """
        # read 64 bytes from the CDI space starting at address zero
        assert isinstance(self._dataProcessor.space, MemorySpace)
        self._dataProcessor.onStartDownload()
        memMemo = MemoryReadMemo(NodeID(farNodeID), 64,
                                 self._dataProcessor.space.value,
                                 0,  # incremented on _memoryReadSuccess
                                 self._memoryReadFail,
                                 self._memoryReadSuccess)
        self._memoryService.requestMemoryRead(memMemo)

    def _default_dl_callback(self, event_d: CDIMemo):
        print(f"[download default callback] {event_d}", file=sys.stderr)

    def download(self, farNodeID: str, space: MemorySpace,
                 dataProcessor: XMLDataProcessor):
        """Download data of any memory space from the remote node.

        Args:
            farNodeID (str): Any valid node ID.
            space (MemorySpace): The memory space to read.
            dataProcessor (XMLDataProcessor): An XMLProcessor or
                subclass, such as cdi_form on downloadCDI in MainForm.

        Raises:
            ValueError: No farNodeID
            RuntimeError: No self._port
            RuntimeError: No self.physicalLayer
        """
        if not farNodeID or not farNodeID.strip():
            raise ValueError("No farNodeID specified.")
        self._farNodeID = farNodeID
        if not self._port:
            raise RuntimeError(
                "No port connection. Call startListening first.")
        if not self.physicalLayer:
            raise RuntimeError(
                "No physicalLayer. Call startListening first.")
        assert isinstance(space, MemorySpace)
        self._dataProcessor = dataProcessor
        self._dataProcessor._space = space

        self._startMemoryRead(farNodeID)
        # ^ Following this, _memoryReadSuccess callback will
        #   trigger requestMemoryRead, completing a
        #   loop until end/fail.

    # def _sendToPort(self, string: str):
    #     # print("      SR: {}".format(string.strip()))
    #     DeprecationWarning("Use a PhysicalLayer subclass' sendFrameAfter")
    #     self.sendFrameAfter(string)

    # def _printFrame(self, frame: CanFrame):
    #     # print("   RL: {}".format(frame))
    #     pass

    def _printDatagram(self, memo: DatagramReceiveMemo):
        """A call-back for when datagrams received

        Args:
            memo (DatagramReceiveMemo): The datagram object

        Returns:
            bool: Always False (True would mean we sent a reply to the
                datagram, but let the MemoryService do that).
        """
        # print("Datagram receive call back: {}".format(memo.data))
        return False

    def _listen(self):
        self._fireStatus("physicalLayerUp...")
        self.physicalLayer.physicalLayerUp()
        self._connectingStart = default_timer()
        self._messageStart = None
        caught_ex = None
        try:
            # NOTE: self._canLink.state is *definitely not*
            #   CanLink.State.Permitted yet, but that's ok because
            #   CanLink's default receiveHandler has to provide
            #   the alias from each node (collision or not)
            #   to has to get the expected replies to the alias
            #   reservation sequence below.
            precise_sleep(.05)   # Wait for physicalLayerUp non-network Message
            while True:
                # Wait 200 ms for all nodes to announce (and for alias
                #   reservation to complete), as per section 6.2.1 of CAN
                #   Frame Transfer Standard (sendMessage requires )
                logger.debug("[_listen] _receive...")
                try:
                    # Receive mode (switches to write mode on BlockingIOError
                    #   which is expected and used on purpose)
                    count = self.physicalLayer.receiveAll(self._port)
                    if count < 1:
                        # BlockingIOError would be raised by
                        #   self._port.receive via self._receive, but
                        #   receiveAll handles the exception (in which
                        #   case return is 0), so switch back to send
                        #   mode manually by raising:
                        raise BlockingIOError("No data yet")

                    # ^ handleData will trigger self._printFrame if that
                    #   was added via registerFrameReceivedListener
                    #   during connect. But now you can use verbose=True
                    #   for receiveAll instead if desired debugging.
                    precise_sleep(.01)  # let processor sleep before read
                    if default_timer() - self._connectingStart > .21:
                        if self.canLink._state != CanLink.State.Permitted:
                            delta = 0
                            if self._messageStart is not None:
                                delta = default_timer() - self._messageStart
                            if ((self._messageStart is None) or (delta > 1)):
                                logger.warning(
                                    "CanLink is not ready yet."
                                    " There must have been a collision"
                                    "--processCollision increments node alias"
                                    " in this case and tries again.")
                        # else _on_link_state_change will be called
                    # TODO: move *all* send calls to this loop.
                except BlockingIOError:
                    # Nothing to receive right now, so perform all sends
                    #   This *must* occur (require socket.setblocking(False))
                    self.physicalLayer.sendAll(self._port)
                    #   so that it doesn't block (or occur during) recv
                    #   (overlapping calls would cause undefined behavior)!
                    # delay = random.uniform(.005,.02)
                    # ^ random delay may help if send is on another thread
                    #   (but avoid that for stability and speed)
                    precise_sleep(.01)
            # raise RuntimeError("We should never get here")
        except RuntimeError as ex:
            caught_ex = ex
            # If _port is a TcpSocket:
            #   May be raised by tcplink.tcpsocket.TCPSocket.receive
            #   manually.
            #   - Usually "socket connection broken" due to no more
            #     bytes to read, but ok if "\0" terminator was reached.
            if self._dataProcessor is not None:
                if ((self._dataProcessor._data is not None)
                        and (not self._dataProcessor._stringTerminated)):
                    # This boolean is managed by the memoryReadSuccess
                    # callback.
                    cm = DataProcessorMemo()
                    cm.error = formatted_ex(ex)
                    cm.done = True  # stop progress in gui/other main thread
                    if self._dataProcessor.onStatusMemo:
                        self._dataProcessor.onStatusMemo(cm)
                    raise  # re-raise since incomplete (prevent done OK state)
            else:
                logger.warning(
                    "Listen loop ended, but _dataProcessor not set"
                    " (DataProcessorMemo will not be used to notify caller).")
            raise
        finally:
            self.physicalLayer.physicalLayerDown()  # Link_Layer_Down, setState
        self._listenThread: Union[threading.Thread, None] = None

        # If we got here, the RuntimeError was ok since the
        #   null terminator '\0' was reached (otherwise re-raise occurs above)
        cm = DataProcessorMemo()
        cm.error = ("Listen loop stopped (caught_ex={})."
                    .format(formatted_ex(caught_ex)))
        cm.done = True
        if not (self._onConnect and self._onConnect(cm)):
            # The message was not handled, so log it.
            logger.error(cm.error)
        return cm  # return it in case running synchronously (no thread)

    def _handleMessage(self, message: Message):
        """Handle a Message from the LCC network.
        The Message Type Indicator (MTI) is checked in case the
        application should visualize a change in the connection state
        etc.

        Data (Memo) is not handled here (See _memoryReadSuccess and
        _memoryReadFail for that).

        Args:
            message (Message): Any message instance received from the
                LCC network.

        Returns:
            bool: If message was handled (always True in this
                method)
        """
        logger.debug("[_handleMessage] RM: {} from {}"
                     .format(message, message.source))
        logger.debug("[_handleMessage]   message.mti={}".format(message.mti))
        if message.mti == MTI.Link_Layer_Down:
            if self._onConnect:
                cm = DataProcessorMemo()
                cm.done = True
                cm.error = "Disconnected"
                cm.message = message
                self._messageStart = None  # so _listen won't discard error
                self._onConnect(cm)
                return True
        elif message.mti == MTI.Link_Layer_Up:
            if self._onConnect:
                cm = DataProcessorMemo()
                cm.done = True  # 'done' without error indicates connected.
                cm.message = message
                self._onConnect(cm)
                return True
        return False

    def _fireStatus(self, status,
                    callback: Union[Callable[[CDIMemo], None], None] = None):
        """Fire status handlers with the given status."""
        if callback is None:
            callback = self._onConnect
        if callback:
            print("OpenLCBNetwork callback_msg({})".format(repr(status)))
            callback(CDIMemo(status=status))
        else:
            logger.warning(
                f"[OpenLCBNetwork] No callback, but set status: {status}")

    def _memoryReadSuccess(self, memo: MemoryReadMemo, force_end=False):
        """Handle a successful read
        Invoked when the memory read successfully returns,
        this queues a new read until the entire CDI has been
        returned.  At that point, it invokes the XML processing below.

        Args:
            memo (MemoryReadMemo): Successful MemoryReadMemo
        """
        # print("successful memory read: {}".format(memo.data))
        if (not force_end) and (len(memo.data) == 64 and 0 not in memo.data):
            # *not* last chunk
            self._dataProcessor._stringTerminated = False
            if self._dataProcessor.format != DataFormat.EOF:
                # save content
                self._dataProcessor._feedNext(memo)
            else:
                logger.error(
                    "Unknown data packet received"
                    " (memory read not triggered by OpenLCBNetwork)")
            # update the address
            memo.address = memo.address + 64
            # and read again (read next)
            self._memoryService.requestMemoryRead(memo)
            # The last packet is not yet reached
        else:  # last chunk
            self._dataProcessor._stringTerminated = True
            # and we're done!
            if self._dataProcessor.format != DataFormat.EOF:
                self._dataProcessor._feedLast(memo)
            else:
                logger.error(
                    "Unknown last data packet received"
                    " (memory read not triggered by OpenLCBNetwork)")
            self._dataProcessor.onStop()
            # done reading

    def _memoryReadFail(self, memo: MemoryReadMemo):
        error = "memory read failed: {}".format(memo.data)
        if self._dataProcessor._onElement:
            if len(self._dataProcessor._tag_stack):
                cm = self._dataProcessor._tag_stack[-1]
            else:
                cm = DataProcessorMemo()
            cm.error = error
            cm.done = True  # stop progress in gui/other main thread
            self._dataProcessor._onElement(cm)
        else:
            logger.error(error)
