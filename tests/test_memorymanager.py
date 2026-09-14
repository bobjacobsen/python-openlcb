import os
import struct
import sys
import time
import unittest
import xml.sax.handler

from typing import Any, Union

from openlcb import emit_cast
from openlcb.canbus.canlink import CanLink
from openlcb.canbus.canphysicallayergridconnect import CanPhysicalLayerGridConnect
from openlcb.cdivar import SIGNED_INT_MINIMUMS, CDIVar
from openlcb.datagramservice import DatagramService, DatagramSendMemo
from openlcb.dataprocessormemo import DataProcessorMemo
from openlcb.localnode import LocalNode
from openlcb.localnodeprocessor import LocalNodeProcessor
from openlcb.memorymanager import MemoryManager, Segment
from openlcb.memoryspace import MemorySpace

from logging import getLogger

from openlcb.memoryreadjob import MemoryReadJob
from openlcb.memoryservice import MemoryReadMemo, MemoryService
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.node import Node
from openlcb.nodeid import generate_node_id
from openlcb.openlcbnetwork import OpenLCBNetwork
from openlcb.pip import PIP
from openlcb.portinterface import PortInterface
from openlcb.snip import SNIP
if __name__ == "__main__":
    logger = getLogger(__file__)
else:
    logger = getLogger(__name__)

if __name__ == "__main__":
    # Allow importing repo copy of openlcb if running tests from repo manually.
    TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
    REPO_DIR = os.path.dirname(TESTS_DIR)
    if os.path.isfile(os.path.join(REPO_DIR, "openlcb", "__init__.py")):
        sys.path.insert(0, REPO_DIR)
    else:
        logger.warning(
            "Reverting to installed copy if present (or imports will fail),"
            " since test running from repo but could not find openlcb in {}."
            .format(repr(REPO_DIR)))

# demo_virtual_node_cdi: same as example_node_memory_implementation.py
demo_virtual_node_cdi = """<?xml version="1.0" encoding="utf-8"?>
<cdi
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://openlcb.org/schema/cdi/1/1/cdi.xsd">
  <identification>
    <manufacturer>python-openlcb example authors</manufacturer>
    <model>example_node_memory_implementation</model>
    <hardwareVersion>1.0</hardwareVersion>
    <softwareVersion>1.0</softwareVersion>
  </identification>
  <acdi/>
  <segment space='0' origin='0'>
    <int size="2">
      <name>Port</name>
      <description>Network port of remote hub (2-byte unsigned short)</description>
      <default>12021</default>
    </int>
    <float size="2">
      <name>Timeout</name>
      <description>Network timeout (2-byte binary16 value).</description>
      <default>0.5</default>
    </float>
  </segment>
</cdi>
"""  # noqa: E501


class MockPort(PortInterface):
    def __init__(self, name="MockPort"):
        PortInterface.__init__(self)
        self.name = name
        self.data = bytearray()  # type: bytearray

    def _settimeout(self, seconds):
        """Abstract method. Return: implementation-specific or None."""
        raise NotImplementedError(
            f"{type(self).__name__} subclass must implement _settimeout.")

    def _connect(self, host: Any, port: Any, device: Any = None):
        """Abstract interface. Return: implementation-specific or None
        See connect for details.
        raise exception on failure to prevent self._open = True.
        """
        pass

    def _send(self, data: Union[bytes, bytearray]) -> None:
        """Abstract method. Return: implementation-specific or None"""
        print("[MockPort] Ran dummy version of _send method.")
        pass

    def _receive(self) -> Union[bytearray, bytes, None]:
        """Abstract method. Return (bytes): data"""
        end = len(self.data)  # concurrency issue mitigation
        data = self.data[:end]
        del self.data[:end]
        if data:
            # GridConnect (hex notation) bytes (already human-readable):
            logger.debug(f"{self.name} Received {len(data)} byte(s): {data}")
            # print(f"{self.name} Received {len(data)} byte(s)")
        return data

    def _close(self) -> None:
        """Abstract method. Return: implementation-specific or None"""
        pass


class TestMemoryManager(unittest.TestCase):

    def testGetNothing(self):
        memory = MemoryManager()
        value_bytes = memory.getSlice(4, 40, 4, force=True)
        self.assertEqual(len(value_bytes), 4)
        value = struct.unpack(">I", value_bytes)[0]
        assert isinstance(value, int)
        # i or I: int32
        # capital letter: unsigned
        self.assertEqual(value, 0)

    def test_get_raises_keyerror(self):
        memory = MemoryManager()
        with self.assertRaises(KeyError):
            # KeyError is necessary because space 4 was not defined
            #   (memory.set* is not called above, so no spaces exist).
            memory.getSlice(4, 40, 4)        # adjust arguments as needed

    def testUnsignedIntData(self):
        in_value = 9999999
        value_bytes = struct.pack(">I", in_value)
        self.assertEqual(len(value_bytes), 4)
        assert isinstance(value_bytes, (bytes, bytearray))
        memory = MemoryManager()
        memory.setSlice(1, 10, value_bytes)
        out_bytes = memory.getSlice(1, 10, 4)
        self.assertEqual(len(out_bytes), 4)
        out_value = struct.unpack(">I", out_bytes)[0]
        self.assertEqual(in_value, out_value)

    def testSignedIntData(self):
        in_value = -9999999
        value_bytes = struct.pack(">i", in_value)
        self.assertEqual(len(value_bytes), 4)
        assert isinstance(value_bytes, (bytes, bytearray))
        memory = MemoryManager()
        memory.setSlice(1, 10, value_bytes)
        out_bytes = memory.getSlice(1, 10, 4)
        self.assertEqual(len(out_bytes), 4)
        out_value = struct.unpack(">i", out_bytes)[0]
        self.assertEqual(in_value, out_value)

    def testUnsignedInt(self):
        in_value = 9999999
        memory = MemoryManager()
        size = 4
        signed = False
        memory.setInt(1, 10, in_value, size, signed)
        out_bytes = memory.getSlice(1, 10, size)
        self.assertEqual(len(out_bytes), size)
        out_value = struct.unpack(">I", out_bytes)[0]
        self.assertEqual(in_value, out_value)
        out_value = memory.getInt(1, 10, size, signed)
        self.assertEqual(in_value, out_value)

    def testSignedInt(self):
        in_value = -9999999
        memory = MemoryManager()
        size = 4
        signed = True
        memory.setInt(1, 10, in_value, size, signed)
        out_bytes = memory.getSlice(1, 10, size)
        self.assertEqual(len(out_bytes), size)
        out_value = struct.unpack(">i", out_bytes)[0]
        self.assertEqual(in_value, out_value)
        out_value = memory.getInt(1, 10, size, signed)
        self.assertEqual(in_value, out_value)

    def testFloat(self):
        memory = MemoryManager()
        sizeFormats = {
            2: ">e",
            4: ">f",
            8: ">d",
        }
        in_value = -999
        size = 2
        memory.setFloat(1, 10, in_value, size)
        out_bytes = memory.getSlice(1, 10, size)
        self.assertEqual(len(out_bytes), size)
        out_value = struct.unpack(sizeFormats[size], out_bytes)[0]
        self.assertEqual(in_value, out_value)
        out_value = memory.getFloat(1, 10, size)
        self.assertEqual(in_value, out_value)

        size = 4
        in_value = -9999999  # NOTE: f32 fits -9999999 f16 does not
        memory.setFloat(1, 10, in_value, size)
        out_bytes = memory.getSlice(1, 10, size)
        self.assertEqual(len(out_bytes), size)
        out_value = struct.unpack(sizeFormats[size], out_bytes)[0]
        self.assertEqual(in_value, out_value)
        out_value = memory.getFloat(1, 10, size)
        self.assertEqual(in_value, out_value)

        size = 8
        memory.setFloat(1, 10, in_value, size)
        out_bytes = memory.getSlice(1, 10, size)
        self.assertEqual(len(out_bytes), size)
        out_value = struct.unpack(sizeFormats[size], out_bytes)[0]
        self.assertEqual(in_value, out_value)
        out_value = memory.getFloat(1, 10, size)
        self.assertEqual(in_value, out_value)

    def testCDIVarUInt(self):
        size = 4
        var = CDIVar("int", _size=size)
        var.space = 1
        var.address = 10
        in_value = 999
        # signed = False
        var.setInt(in_value)
        self.assertEqual(var.getInt(), in_value)
        memory = MemoryManager()
        memory.set(var)
        var = memory.get(var)
        self.assertEqual(var.getInt(), in_value)
        assert var.space is not None
        assert var.address is not None
        assert var.size is not None
        assert var.signed is not None
        out_value = memory.getInt(var.space, var.address, var.size, var.signed)
        self.assertEqual(out_value, in_value)

    def testCDIVarSInt(self):
        size = 4
        in_value = -999
        signed = True if in_value < 0 else False
        # defaultVar = CDIVar("int", _size=size, _no_min=True, _no_max=True,
        #                     signed=signed)
        # defaultVar.setInt(in_value)
        # simplified construction:
        defaultVar = CDIVar.fromInt(in_value, size)
        self.assertTrue(defaultVar.signed)
        self.assertIsNone(defaultVar.min)
        var = CDIVar(
            "int",
            _size=size,
            _default=defaultVar,  # forces signed since negative
        )
        self.assertTrue(var.signed)
        self.assertIsInstance(var.min, CDIVar)
        self.assertIsNotNone(
            var.min,
            msg=f"{emit_cast(var.min)} should be min for {size*8}-bit")
        self.assertEqual(var.min, SIGNED_INT_MINIMUMS[size])
        # ^ == allowed since __eq__ is defined for CDIVar (var.min)
        var.space = 1
        var.address = 10
        # signed = False
        var.setInt(in_value)
        self.assertEqual(var.getInt(), in_value)
        memory = MemoryManager()
        memory.set(var)
        var = memory.get(var)
        self.assertEqual(var.getInt(), in_value)
        assert var.space is not None
        assert var.address is not None
        assert var.size is not None
        assert var.signed is True
        out_value = memory.getInt(var.space, var.address, var.size, var.signed)
        self.assertEqual(out_value, in_value)

    def testGetCDI(self):
        def readReply(memo: MemoryReadMemo):
            print(f"GOT: {memo.data}")

        def readRejected(memo: MemoryReadMemo):
            print(f"REJECTED: {memo}")

        localNodeID = generate_node_id("05.01.05")  # "05.01.01" is only for OpenLCB Group. See <https://registry.openlcb.org/uniqueidranges>  # noqa: E501
        network = OpenLCBNetwork(localNodeID)
        localNode = Node(
            localNodeID,
            SNIP("python-openlcb authors",
                 "test_memorymanager CT",
                 "1.0", "1.0", "test_memorymanager CT",
                 "python-openlcb configuration tool for test_memorymanager"),
            set([
                PIP.SIMPLE_NODE_IDENTIFICATION_PROTOCOL,
                PIP.DATAGRAM_PROTOCOL,
                PIP.CONFIGURATION_DESCRIPTION_INFORMATION,
                PIP.ADCDI_PROTOCOL,
                PIP.MEMORY_CONFIGURATION_PROTOCOL,
            ])
        )
        # ^ Same as (Except SNIP not necessary for CT if MemoryManager isn't used):

        virtualPhysicalLayer = CanPhysicalLayerGridConnect()

        mockLocalPort = MockPort(name="localMockPort")
        virtualMockPort = MockPort(name="virtualMockPort")

        network._port = mockLocalPort

        def local_send(data):
            """Make physicalLayer into loopback device"""
            virtualMockPort.data += data

        def virtual_send(data):
            mockLocalPort.data += data

        # Setup loopback:
        virtualMockPort.send = virtual_send
        mockLocalPort.send = local_send

        virtualNodeID = generate_node_id("05.01.05", increment=True)  # "05.01.01" is only for OpenLCB Group. See <https://registry.openlcb.org/uniqueidranges>  # noqa: E501
        assert virtualNodeID != localNodeID

        print(f"localNodeID: {localNodeID}")
        print(f"virtualNodeID: {virtualNodeID}")

        virtualCanLink = CanLink(virtualPhysicalLayer, virtualNodeID)

        virtualNode = LocalNode(
            virtualNodeID,
            virtualCanLink,
            snip=SNIP("python-openlcb authors",
                      "test_memorymanager VN",
                      "1.0", "1.0", "test_memorymanager VN",
                      "python-openlcb virtual node with memory for test_memorymanager"),  # noqa: E501
            pipSet=set([
                PIP.SIMPLE_NODE_IDENTIFICATION_PROTOCOL,
                PIP.DATAGRAM_PROTOCOL,
                PIP.CONFIGURATION_DESCRIPTION_INFORMATION,
                PIP.ADCDI_PROTOCOL,
                PIP.MEMORY_CONFIGURATION_PROTOCOL,
            ]),
        )
        # dgService = DatagramService(canLink)
        # localMemoryService = MemoryService(dgService)
        virtualNodeProcessor = LocalNodeProcessor(virtualCanLink, virtualNode)
        virtualCanLink.registerMessageReceivedListener(
            virtualNodeProcessor.process)
        virtualDGService = DatagramService(virtualCanLink)
        virtualCanLink.registerMessageReceivedListener(
            virtualDGService.process)

        def debug_virtual_incoming(memo):
            logger.debug(
                f"🔍 VIRTUAL RECEIVED DATAGRAM: {type(memo).__name__} - {memo}")

        # def debug_virtual_outgoing(memo):
        #     print(f"📤 VIRTUAL SENDING REPLY: {memo}")

        virtualDGService.registerDatagramReceivedListener(
            debug_virtual_incoming)

        def debug_local_reply(memo):
            logger.debug(f"🔙 LOCAL RECEIVED REPLY: {memo}")

        network._datagramService.registerDatagramReceivedListener(
            debug_local_reply)

        virtualMemoryService = MemoryService(virtualDGService)
        virtualMemoryService.memory = virtualNode
        # virtualNode.loadCDIString(demo_virtual_node_cdi, __file__)
        # ^ commented since creates unnecessary files in this case,
        #   such as tests/05.01.05.BB.B4.2A.lcc-link-virtual-node.space=0.xml
        virtualNode.loadCDIString(demo_virtual_node_cdi, None)
        got = virtualNode.getSlice(MemorySpace.CDI,
                                   0, len(demo_virtual_node_cdi))
        segment = virtualNode.getSegment(MemorySpace.CDI)  # type: Segment|None
        assert isinstance(segment, Segment)
        assert isinstance(segment._data, (bytearray, bytes))
        assert got.decode() == demo_virtual_node_cdi

        assert segment._data == demo_virtual_node_cdi.encode()
        # ^ not itself threaded, so no memo for callback is necessary
        #   network.startListening(mockLocalPort)
        #   commenting this requires your own physicalLayerUp
        #   and listen loop (sendAll and receiveAll calls)

        last = virtualNode.getLast(0xFF)
        assert last is not None
        last = virtualNode.getLast(MemorySpace.CDI)
        assert last is not None

        network.physicalLayer.physicalLayerUp()
        virtualPhysicalLayer.physicalLayerUp()

        localState = network.canLink.pollState()
        network._port = None  # since using manual sendAll and receiveAll
        while localState != CanLink.State.Permitted:
            network.physicalLayer.sendAll(mockLocalPort)
            network.physicalLayer.receiveAll(mockLocalPort)
            virtualPhysicalLayer.sendAll(virtualMockPort)
            virtualPhysicalLayer.receiveAll(virtualMockPort)
            # NOTE: startListening will be doing sendAll and receiveAll
            #   for network.physicalLayer in another thread.
            print(f"Waiting for Permitted (state={localState})")
            localState = network.canLink.pollState()
            time.sleep(.02)
        print(f"Network state is {localState}")

        virtualState = virtualCanLink.pollState()
        while True:
            network.physicalLayer.sendAll(mockLocalPort)
            network.physicalLayer.receiveAll(mockLocalPort)
            virtualPhysicalLayer.sendAll(virtualMockPort)
            virtualPhysicalLayer.receiveAll(virtualMockPort)
            # NOTE: startListening will be doing sendAll and receiveAll
            #   for network.physicalLayer in another thread.
            network.canLink.pollState()
            virtualState = virtualCanLink.pollState()
            if virtualState == CanLink.State.Permitted:
                if virtualNodeID in network.canLink.nodeIdToAlias:
                    break
                else:
                    print(
                        f"Waiting for alias {virtualNodeID}"
                        f" in {network.canLink.nodeIdToAlias}...")
            else:
                print(f"Waiting for virtual Permitted (state={virtualState})")
            time.sleep(.02)

        print(f"Virtual network state is {localState}")

        localNodeProcessor = LocalNodeProcessor(
            network.canLink, localNode)
        network.canLink.registerMessageReceivedListener(
            localNodeProcessor.process)

        def displayOtherNodeIds(message: Message) :
            """Listener to identify connected nodes

            Args:
                message (Message): A response from the network
            """
            print(f"[displayOtherNodeIds] {type(message).__name__}: {message.mti}")
            if message.mti == MTI.Verified_NodeID :
                print("Detected farNodeID is {}".format(message.source))

        network.canLink.registerMessageReceivedListener(displayOtherNodeIds)

        job = MemoryReadJob(network._memoryService)

        class DummyHandler(xml.sax.handler.ContentHandler):
            pass

        handler = DummyHandler()

        done = False

        def statusCallback(memo: DataProcessorMemo):
            nonlocal done
            print(f"statusCallback(memo): {memo.status}")
            done = memo.done

        job.readMemory(network.canLink, virtualNodeID, MemorySpace.CDI,
                       handler=handler,
                       callback=statusCallback)
        while not done:
            if job.failed:
                print(f"MemoryReadJob failed"
                      f" (expected {len(demo_virtual_node_cdi)} byte(s))")
                break
            if job.completeData:
                print("MemoryReadJob completed")
                break
            network.physicalLayer.sendAll(mockLocalPort)
            network.physicalLayer.receiveAll(mockLocalPort)
            virtualPhysicalLayer.sendAll(virtualMockPort)
            virtualPhysicalLayer.receiveAll(virtualMockPort)
            assert network._port is mockLocalPort or network._port is None
            # NOTE: startListening will be doing sendAll and receiveAll
            #   for network.physicalLayer in another thread.
            localState = network.canLink.pollState()
            virtualState = virtualCanLink.pollState()
            if localState != CanLink.State.Permitted:
                print(f"Warning: local network state is {localState}")
            if virtualState != CanLink.State.Permitted:
                print(f"Warning: virtual network state is {virtualState}")
            print("Waiting for done...")
            time.sleep(.02)


if __name__ == "__main__":
    unittest.main()
