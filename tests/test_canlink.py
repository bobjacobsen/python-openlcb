import unittest

from openlcb.canbus.canlink import CanLink

from openlcb.canbus.canframe import CanFrame
from openlcb.canbus.canphysicallayer import CanPhysicalLayer
from openlcb.canbus.canphysicallayersimulation import CanPhysicalLayerSimulation
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.nodeid import NodeID
from openlcb.canbus.controlframe import ControlFrame


class PhyMockLayer(CanPhysicalLayer):
    def __init__(self):
        self.receivedFrames = []
        CanPhysicalLayer.__init__(self)

    def sendCanFrame(self, frame):
        self.receivedFrames.append(frame)


class MessageMockLayer:
    '''Mock Message to record messages requested to be sent'''
    def __init__(self):
        self.receivedMessages = []

    def receiveMessage(self, msg):
        self.receivedMessages.append(msg)


class TestCanLinkClass(unittest.TestCase):

    # MARK: - Alias calculations
    def testIncrementAlias48(self):
        canLink = CanLink(NodeID("05.01.01.01.03.01"))

        # check precision of calculation
        self.assertEqual(canLink.incrementAlias48(0), 0x1B0C_A37A_4BA9,
                         "0 initial value")

        # test shift and multiplication operations
        next = canLink.incrementAlias48(0x0000_0000_0001)
        self.assertEqual(next, 0x1B0C_A37A_4DAA)

    def testIncrementAliasSequence(self):
        canLink = CanLink(NodeID("05.01.01.01.03.01"))

        # sequence from TN
        next = canLink.incrementAlias48(0)
        self.assertEqual(next, 0x1B0C_A37A_4BA9, "0 initial value")

        next = canLink.incrementAlias48(next)
        self.assertEqual(next, 0x4F_60_3B_8B_E9_52)

        next = canLink.incrementAlias48(next)
        self.assertEqual(next, 0x2A_E3_F6_D8_D8_FB)

        next = canLink.incrementAlias48(next)
        self.assertEqual(next, 0x0D_DE_4C_05_1A_A4)

        next = canLink.incrementAlias48(next)
        self.assertEqual(next, 0xE5_82_F9_B4_AE_4D)

    def testCreateAlias12(self):
        canLink = CanLink(NodeID("05.01.01.01.03.01"))

        # check precision of calculation
        self.assertEqual(canLink.createAlias12(0x001), 0x001, "0x001 input")
        self.assertEqual(canLink.createAlias12(0x1_000), 0x001, "0x1000 input")
        self.assertEqual(canLink.createAlias12(0x1_000_000), 0x001,
                         "0x1000000 input")

        self.assertEqual(canLink.createAlias12(0x4_002_001), 0x007)

        self.assertEqual(canLink.createAlias12(0x1001), 0x002,
                         "0x1001 random input checks against zero")

        self.assertEqual(canLink.createAlias12(0x0000), 0xAEF,
                         "zero input check")

    # MARK: - Test PHY Up
    def testLinkUpSequence(self):
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        messageLayer = MessageMockLayer()
        canLink.registerMessageReceivedListener(messageLayer.receiveMessage)

        canPhysicalLayer.physicalLayerUp()

        self.assertEqual(len(canPhysicalLayer.receivedFrames), 7)
        self.assertEqual(canLink.state, CanLink.State.Permitted)

        self.assertEqual(len(messageLayer.receivedMessages), 1)

    # MARK: - Test PHY Down, Up, Error Information
    def testLinkDownSequence(self):
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        messageLayer = MessageMockLayer()
        canLink.registerMessageReceivedListener(messageLayer.receiveMessage)
        canLink.state = CanLink.State.Permitted

        canPhysicalLayer.physicalLayerDown()

        self.assertEqual(canLink.state, CanLink.State.Inhibited)
        self.assertEqual(len(messageLayer.receivedMessages), 1)

    def testAEIE2noData(self):
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        canLink.state = CanLink.State.Permitted

        canPhysicalLayer.fireListeners(CanFrame(ControlFrame.EIR2.value, 0))
        self.assertEqual(len(canPhysicalLayer.receivedFrames), 0)

    # MARK: - Test AME (Local Node)
    def testAMEnoData(self):
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        ourAlias = canLink.localAlias  # 576 with NodeID(0x05_01_01_01_03_01)
        canLink.state = CanLink.State.Permitted

        canPhysicalLayer.fireListeners(CanFrame(ControlFrame.AME.value, 0))
        self.assertEqual(len(canPhysicalLayer.receivedFrames), 1)
        self.assertEqual(
            canPhysicalLayer.receivedFrames[0],
            CanFrame(ControlFrame.AMD.value, ourAlias,
                     canLink.localNodeID.toArray())
        )

    def testAMEnoDataInhibited(self):
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        canLink.state = CanLink.State.Inhibited

        canPhysicalLayer.fireListeners(CanFrame(ControlFrame.AME.value, 0))
        self.assertEqual(len(canPhysicalLayer.receivedFrames), 0)

    def testAMEMatchEvent(self):
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        ourAlias = canLink.localAlias  # 576 with NodeID(0x05_01_01_01_03_01)
        canLink.linkPhysicalLayer(canPhysicalLayer)
        canLink.state = CanLink.State.Permitted

        frame = CanFrame(ControlFrame.AME.value, 0)
        frame.data = [5, 1, 1, 1, 3, 1]
        canPhysicalLayer.fireListeners(frame)
        self.assertEqual(len(canPhysicalLayer.receivedFrames), 1)
        self.assertEqual(canPhysicalLayer.receivedFrames[0],
                         CanFrame(ControlFrame.AMD.value, ourAlias,
                                  canLink.localNodeID.toArray()))

    def testAMEnotMatchEvent(self):
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        canLink.state = CanLink.State.Permitted

        frame = CanFrame(ControlFrame.AME.value, 0)
        frame.data = [0, 0, 0, 0, 0, 0]
        canPhysicalLayer.fireListeners(frame)
        self.assertEqual(len(canPhysicalLayer.receivedFrames), 0)

    # MARK: - Test Alias Collisions (Local Node)
    def testCIDreceivedMatch(self):
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        ourAlias = canLink.localAlias  # 576 with NodeID(0x05_01_01_01_03_01)
        canLink.linkPhysicalLayer(canPhysicalLayer)
        canLink.state = CanLink.State.Permitted

        canPhysicalLayer.fireListeners(CanFrame(7, canLink.localNodeID,
                                                ourAlias))
        self.assertEqual(len(canPhysicalLayer.receivedFrames), 1)
        self.assertEqual(canPhysicalLayer.receivedFrames[0],
                         CanFrame(ControlFrame.RID.value, ourAlias))

    def testRIDreceivedMatch(self):
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        ourAlias = canLink.localAlias  # 576 with NodeID(0x05_01_01_01_03_01)
        canLink.linkPhysicalLayer(canPhysicalLayer)
        canLink.state = CanLink.State.Permitted

        canPhysicalLayer.fireListeners(CanFrame(ControlFrame.RID.value,
                                                ourAlias))
        self.assertEqual(len(canPhysicalLayer.receivedFrames), 8)
        # ^ includes recovery of new alias 4 CID, RID, AMR, AME
        self.assertEqual(canPhysicalLayer.receivedFrames[0],
                         CanFrame(ControlFrame.AMR.value, ourAlias,
                                  [5, 1, 1, 1, 3, 1]))
        self.assertEqual(canPhysicalLayer.receivedFrames[6],
                         CanFrame(ControlFrame.AMD.value, 0x539,
                                  [5, 1, 1, 1, 3, 1]))  # new alias
        self.assertEqual(canLink.state, CanLink.State.Permitted)

    def testCheckMTImapping(self):

        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        self.assertEqual(
            canLink.canHeaderToFullFormat(CanFrame(0x19490247, [])),
            MTI.Verify_NodeID_Number_Global
        )

    def testControlFrameDecode(self):
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        frame = CanFrame(0x1000, 0x000)  # invalid control frame content
        self.assertEqual(canLink.decodeControlFrameFormat(frame),
                         ControlFrame.UnknownFormat)

    def testSimpleGlobalData(self):
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        messageLayer = MessageMockLayer()
        canLink.registerMessageReceivedListener(messageLayer.receiveMessage)
        canLink.state = CanLink.State.Permitted

        # map an alias we'll use
        amd = CanFrame(0x0701, 0x247)
        amd.data = [1, 2, 3, 4, 5, 6]
        canPhysicalLayer.fireListeners(amd)

        canPhysicalLayer.fireListeners(CanFrame(0x19490, 0x247))
        # ^ from previously seen alias

        self.assertEqual(len(canPhysicalLayer.receivedFrames), 0)
        # ^ nothing back down to CAN
        self.assertEqual(len(messageLayer.receivedMessages), 1)
        # ^ one message forwarded
        # check for proper global MTI
        self.assertEqual(messageLayer.receivedMessages[0].mti,
                         MTI.Verify_NodeID_Number_Global)
        self.assertEqual(messageLayer.receivedMessages[0].source,
                         NodeID(0x010203040506))

    def testVerifiedNodeInDestAliasMap(self):
        # JMRI doesn't send AMD, so gets assigned 00.00.00.00.00.00
        # This tests that a VerifiedNode will update that.

        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        messageLayer = MessageMockLayer()
        canLink.registerMessageReceivedListener(messageLayer.receiveMessage)
        canLink.state = CanLink.State.Permitted

        # Don't map an alias with an AMD for this test

        canPhysicalLayer.fireListeners(CanFrame(0x19170, 0x247,
                                                [8, 7, 6, 5, 4, 3]))
        # ^ VerifiedNodeID from unique alias

        self.assertEqual(len(canPhysicalLayer.receivedFrames), 0)
        # ^ nothing back down to CAN
        self.assertEqual(len(messageLayer.receivedMessages), 1)
        # ^ one message forwarded
        # check for proper global MTI
        self.assertEqual(messageLayer.receivedMessages[0].mti,
                         MTI.Verified_NodeID)
        self.assertEqual(messageLayer.receivedMessages[0].source,
                         NodeID(0x080706050403))

    def testNoDestInAliasMap(self):
        '''Tests handling of a message with a destination alias not in map
        (should not happen, but...)
        '''

        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        messageLayer = MessageMockLayer()
        canLink.registerMessageReceivedListener(messageLayer.receiveMessage)
        canLink.state = CanLink.State.Permitted

        # Don't map an alias with an AMD for this test

        canPhysicalLayer.fireListeners(CanFrame(0x19968, 0x247,
                                                [8, 7, 6, 5, 4, 3]))
        # ^ Identify Events Addressed from unique alias

        self.assertEqual(len(canPhysicalLayer.receivedFrames), 0)
        # ^ nothing back down to CAN
        self.assertEqual(len(messageLayer.receivedMessages), 1)
        # ^ one message forwarded
        # check for proper global MTI
        self.assertEqual(messageLayer.receivedMessages[0].mti,
                         MTI.Identify_Events_Addressed)
        self.assertEqual(messageLayer.receivedMessages[0].source,
                         NodeID(0x000000000001))

    def testSimpleAddressedData(self):  # Test start=yes, end=yes frame
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        messageLayer = MessageMockLayer()
        canLink.registerMessageReceivedListener(messageLayer.receiveMessage)

        canPhysicalLayer.physicalLayerUp()

        # map an alias we'll use
        amd = CanFrame(0x0701, 0x247)
        amd.data = [1, 2, 3, 4, 5, 6]
        canPhysicalLayer.fireListeners(amd)

        ourAlias = canLink.localAlias  # 576 with NodeID(0x05_01_01_01_03_01)
        frame = CanFrame(0x19488, 0x247)  # Verify Node ID Addressed
        frame.data = [((ourAlias & 0x700) >> 8), (ourAlias & 0xFF), 12, 13]
        canPhysicalLayer.fireListeners(frame)  # from previously seen alias

        self.assertEqual(len(messageLayer.receivedMessages), 2)
        # ^ startup plus one message forwarded
        # check for proper global MTI
        self.assertEqual(messageLayer.receivedMessages[1].mti,
                         MTI.Verify_NodeID_Number_Addressed)
        self.assertEqual(messageLayer.receivedMessages[1].source,
                         NodeID(0x01_02_03_04_05_06))
        self.assertEqual(messageLayer.receivedMessages[1].destination,
                         NodeID(0x05_01_01_01_03_01))
        self.assertEqual(len(messageLayer.receivedMessages[1].data), 2)
        self.assertEqual(messageLayer.receivedMessages[1].data[0], 12)
        self.assertEqual(messageLayer.receivedMessages[1].data[1], 13)

    def testSimpleAddressedDataNoAliasYet(self):
        '''Test start=yes, end=yes frame with no alias match'''
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        messageLayer = MessageMockLayer()
        canLink.registerMessageReceivedListener(messageLayer.receiveMessage)

        canPhysicalLayer.physicalLayerUp()

        # don't map alias with AMD

        # send Verify Node ID Addressed from unknown alias
        ourAlias = canLink.localAlias  # 576 with NodeID(0x05_01_01_01_03_01)
        frame = CanFrame(0x19488, 0x247)  # Verify Node ID Addressed
        frame.data = [((ourAlias & 0x700) >> 8), (ourAlias & 0xFF), 12, 13]
        canPhysicalLayer.fireListeners(frame)  # from previously seen alias

        self.assertEqual(len(messageLayer.receivedMessages), 2)
        # ^ startup plus one message forwarded

        # check for proper global MTI
        self.assertEqual(messageLayer.receivedMessages[1].mti,
                         MTI.Verify_NodeID_Number_Addressed)
        self.assertEqual(messageLayer.receivedMessages[1].source,
                         NodeID(0x00_00_00_00_00_01))
        self.assertEqual(messageLayer.receivedMessages[1].destination,
                         NodeID(0x05_01_01_01_03_01))
        self.assertEqual(len(messageLayer.receivedMessages[1].data), 2)
        self.assertEqual(messageLayer.receivedMessages[1].data[0], 12)
        self.assertEqual(messageLayer.receivedMessages[1].data[1], 13)

    def testMultiFrameAddressedData(self):
        '''multi-frame addressed messages - SNIP reply
        Test message in 3 frames
        '''
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        messageLayer = MessageMockLayer()
        canLink.registerMessageReceivedListener(messageLayer.receiveMessage)

        canPhysicalLayer.physicalLayerUp()

        # map an alias we'll use
        amd = CanFrame(0x0701, 0x247)
        amd.data = [1, 2, 3, 4, 5, 6]
        canPhysicalLayer.fireListeners(amd)

        ourAlias = canLink.localAlias  # 576 with NodeID(0x05_01_01_01_03_01)
        frame = CanFrame(0x19488, 0x247)  # Verify Node ID Addressed
        frame.data = [(((ourAlias & 0x700) >> 8) | 0x10),
                      (ourAlias & 0xFF), 1, 2]
        # ^ start not end
        canPhysicalLayer.fireListeners(frame)  # from previously seen alias

        self.assertEqual(len(messageLayer.receivedMessages), 1)
        # ^ startup only, no message forwarded yet

        frame = CanFrame(0x19488, 0x247)  # Verify Node ID Addressed
        frame.data = [(((ourAlias & 0x700) >> 8) | 0x20), (ourAlias & 0xFF),
                      3, 4]
        # ^ end, not start
        canPhysicalLayer.fireListeners(frame)  # from previously seen alias

        self.assertEqual(len(messageLayer.receivedMessages), 2)
        # ^ startup plus one message forwarded

        # check for proper global MTI
        self.assertEqual(messageLayer.receivedMessages[1].mti,
                         MTI.Verify_NodeID_Number_Addressed)
        self.assertEqual(messageLayer.receivedMessages[1].source,
                         NodeID(0x01_02_03_04_05_06))
        self.assertEqual(messageLayer.receivedMessages[1].destination,
                         NodeID(0x05_01_01_01_03_01))

    def testSimpleDatagrm(self):  # Test start=yes, end=yes frame
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        messageLayer = MessageMockLayer()
        canLink.registerMessageReceivedListener(messageLayer.receiveMessage)

        canPhysicalLayer.physicalLayerUp()

        # map two aliases we'll use
        amd = CanFrame(0x0701, 0x247)
        amd.data = [1, 2, 3, 4, 5, 6]
        canPhysicalLayer.fireListeners(amd)
        amd = CanFrame(0x0701, 0x123)
        amd.data = [6, 5, 4, 3, 2, 1]
        canPhysicalLayer.fireListeners(amd)

        frame = CanFrame(0x1A123, 0x247)  # single frame datagram
        frame.data = [10, 11, 12, 13]
        canPhysicalLayer.fireListeners(frame)  # from previously seen alias

        self.assertEqual(len(messageLayer.receivedMessages), 2)
        # ^ startup plus one message forwarded
        # check for proper global MTI
        self.assertEqual(messageLayer.receivedMessages[1].mti,
                         MTI.Datagram)
        self.assertEqual(messageLayer.receivedMessages[1].source,
                         NodeID(0x01_02_03_04_05_06))
        self.assertEqual(messageLayer.receivedMessages[1].destination,
                         NodeID(0x06_05_04_03_02_01))
        self.assertEqual(len(messageLayer.receivedMessages[1].data), 4)
        self.assertEqual(messageLayer.receivedMessages[1].data[0], 10)
        self.assertEqual(messageLayer.receivedMessages[1].data[1], 11)
        self.assertEqual(messageLayer.receivedMessages[1].data[2], 12)
        self.assertEqual(messageLayer.receivedMessages[1].data[3], 13)

    def testThreeFrameDatagrm(self):
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)
        messageLayer = MessageMockLayer()
        canLink.registerMessageReceivedListener(messageLayer.receiveMessage)

        canPhysicalLayer.physicalLayerUp()

        # map two aliases we'll use
        amd = CanFrame(0x0701, 0x247)
        amd.data = [1, 2, 3, 4, 5, 6]
        canPhysicalLayer.fireListeners(amd)
        amd = CanFrame(0x0701, 0x123)
        amd.data = [6, 5, 4, 3, 2, 1]
        canPhysicalLayer.fireListeners(amd)

        frame = CanFrame(0x1B123, 0x247)  # single frame datagram
        frame.data = [10, 11, 12, 13]
        canPhysicalLayer.fireListeners(frame)  # from previously seen alias
        frame = CanFrame(0x1C123, 0x247)  # single frame datagram
        frame.data = [20, 21, 22, 23]
        canPhysicalLayer.fireListeners(frame)  # from previously seen alias
        frame = CanFrame(0x1D123, 0x247)  # single frame datagram
        frame.data = [30, 31, 32, 33]
        canPhysicalLayer.fireListeners(frame)  # from previously seen alias

        self.assertEqual(len(messageLayer.receivedMessages), 2)
        # ^ startup plus one message forwarded
        # check for proper global MTI
        self.assertEqual(messageLayer.receivedMessages[1].mti,
                         MTI.Datagram)
        self.assertEqual(messageLayer.receivedMessages[1].source,
                         NodeID(0x01_02_03_04_05_06))
        self.assertEqual(messageLayer.receivedMessages[1].destination,
                         NodeID(0x06_05_04_03_02_01))
        self.assertEqual(len(messageLayer.receivedMessages[1].data), 12)
        self.assertEqual(messageLayer.receivedMessages[1].data[0], 10)
        self.assertEqual(messageLayer.receivedMessages[1].data[1], 11)
        self.assertEqual(messageLayer.receivedMessages[1].data[2], 12)
        self.assertEqual(messageLayer.receivedMessages[1].data[3], 13)
        self.assertEqual(messageLayer.receivedMessages[1].data[4], 20)
        self.assertEqual(messageLayer.receivedMessages[1].data[5], 21)
        self.assertEqual(messageLayer.receivedMessages[1].data[6], 22)
        self.assertEqual(messageLayer.receivedMessages[1].data[7], 23)
        self.assertEqual(messageLayer.receivedMessages[1].data[8], 30)
        self.assertEqual(messageLayer.receivedMessages[1].data[9], 31)
        self.assertEqual(messageLayer.receivedMessages[1].data[10], 32)
        self.assertEqual(messageLayer.receivedMessages[1].data[11], 33)

    def testZeroLengthDatagram(self):
        canPhysicalLayer = PhyMockLayer()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)

        message = Message(MTI.Datagram, NodeID("05.01.01.01.03.01"),
                          NodeID("05.01.01.01.03.01"))

        canLink.sendMessage(message)

        self.assertEqual(len(canPhysicalLayer.receivedFrames), 1)
        self.assertEqual(str(canPhysicalLayer.receivedFrames[0]),
                         "CanFrame header: 0x1A000000 []")

    def testOneFrameDatagram(self):
        canPhysicalLayer = PhyMockLayer()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)

        message = Message(MTI.Datagram, NodeID("05.01.01.01.03.01"),
                          NodeID("05.01.01.01.03.01"),
                          [1, 2, 3, 4, 5, 6, 7, 8])

        canLink.sendMessage(message)

        self.assertEqual(len(canPhysicalLayer.receivedFrames), 1)
        self.assertEqual(
            str(canPhysicalLayer.receivedFrames[0]),
            "CanFrame header: 0x1A000000 [1, 2, 3, 4, 5, 6, 7, 8]"
        )

    def testTwoFrameDatagram(self):
        canPhysicalLayer = PhyMockLayer()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)

        message = Message(MTI.Datagram, NodeID("05.01.01.01.03.01"),
                          NodeID("05.01.01.01.03.01"),
                          [1, 2, 3, 4, 5, 6, 7, 8,
                           9, 10, 11, 12, 13, 14, 15, 16])

        canLink.sendMessage(message)

        self.assertEqual(len(canPhysicalLayer.receivedFrames), 2)
        self.assertEqual(
            str(canPhysicalLayer.receivedFrames[0]),
            "CanFrame header: 0x1B000000 [1, 2, 3, 4, 5, 6, 7, 8]"
        )
        self.assertEqual(
            str(canPhysicalLayer.receivedFrames[1]),
            "CanFrame header: 0x1D000000 [9, 10, 11, 12, 13, 14, 15, 16]"
        )

    def testThreeFrameDatagram(self):
        canPhysicalLayer = PhyMockLayer()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        canLink.linkPhysicalLayer(canPhysicalLayer)

        message = Message(MTI.Datagram, NodeID("05.01.01.01.03.01"),
                          NodeID("05.01.01.01.03.01"),
                          [1, 2, 3, 4, 5, 6, 7, 8,
                           9, 10, 11, 12, 13, 14, 15, 16,
                           17, 18, 19])

        canLink.sendMessage(message)

        self.assertEqual(len(canPhysicalLayer.receivedFrames), 3)
        self.assertEqual(
            str(canPhysicalLayer.receivedFrames[0]),
            "CanFrame header: 0x1B000000 [1, 2, 3, 4, 5, 6, 7, 8]"
        )
        self.assertEqual(
            str(canPhysicalLayer.receivedFrames[1]),
            "CanFrame header: 0x1C000000 [9, 10, 11, 12, 13, 14, 15, 16]"
        )
        self.assertEqual(str(canPhysicalLayer.receivedFrames[2]),
                         "CanFrame header: 0x1D000000 [17, 18, 19]")

    # MARK: - Test Remote Node Alias Tracking
    def testAmdAmrSequence(self):
        canPhysicalLayer = CanPhysicalLayerSimulation()
        canLink = CanLink(NodeID("05.01.01.01.03.01"))
        ourAlias = canLink.localAlias  # 576 with NodeID(0x05_01_01_01_03_01)
        canLink.linkPhysicalLayer(canPhysicalLayer)

        canPhysicalLayer.fireListeners(CanFrame(0x0701, ourAlias+1))
        # ^ AMD from some other alias

        self.assertEqual(len(canLink.aliasToNodeID), 1)
        self.assertEqual(len(canLink.nodeIdToAlias), 1)

        self.assertEqual(len(canPhysicalLayer.receivedFrames), 0)
        # ^ nothing back down to CAN

        canPhysicalLayer.fireListeners(CanFrame(0x0703, ourAlias+1))
        # ^ AMR from some other alias

        self.assertEqual(len(canLink.aliasToNodeID), 0)
        self.assertEqual(len(canLink.nodeIdToAlias), 0)

        self.assertEqual(len(canPhysicalLayer.receivedFrames), 0)
        # ^ nothing back down to CAN

    # MARK: - Data size handling
    def testSegmentAddressedDataArray(self):
        canLink = CanLink( NodeID("05.01.01.01.03.01"))

        # no data
        self.assertEqual(canLink.segmentAddressedDataArray((0x123), []), [[0x1,0x23]])

        # short data
        self.assertEqual(canLink.segmentAddressedDataArray((0x123), [0x1, 0x2]), [[0x1,0x23, 0x01, 0x02]])

        # full first frame
        self.assertEqual(canLink.segmentAddressedDataArray((0x123), [0x1, 0x2, 0x3, 0x4, 0x5, 0x6]), [[0x1,0x23, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6]])

        # two frames needed
        self.assertEqual(canLink.segmentAddressedDataArray((0x123), [0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7]), [[0x11,0x23, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6], [0x21,0x23, 0x7]])

        # two full frames needed
        self.assertEqual(canLink.segmentAddressedDataArray((0x123), [0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xA, 0xB, 0xC]),
                       [[0x11,0x23, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6], [0x21,0x23, 0x7, 0x8, 0x9, 0xA, 0xB, 0xC]])

        # three frames needed
        self.assertEqual(canLink.segmentAddressedDataArray((0x123), [0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xA, 0xB, 0xC, 0xD, 0xE]),
                       [[0x11,0x23, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6], [0x31,0x23, 0x7, 0x8, 0x9, 0xA, 0xB, 0xC], [0x21, 0x23, 0xD, 0xE]])

    def testSegmentDatagramDataArray(self):
        canLink = CanLink(NodeID("05.01.01.01.03.01"))

        # no data
        self.assertEqual(canLink.segmentDatagramDataArray([]), [[]])

        # short data
        self.assertEqual(canLink.segmentDatagramDataArray([0x1, 0x2]), [[0x01, 0x02]])

        # partially full first frame
        self.assertEqual(canLink.segmentDatagramDataArray([0x1, 0x2, 0x3, 0x4, 0x5, 0x6]), [[0x1, 0x2, 0x3, 0x4, 0x5, 0x6]])

        # one full frame needed
        self.assertEqual(canLink.segmentDatagramDataArray([0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8]), [[0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8]])

        # two frames needed
        self.assertEqual(canLink.segmentDatagramDataArray([0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9]), [[0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8], [0x9]])

        # two full frames needed
        self.assertEqual(canLink.segmentDatagramDataArray([0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF, 0x10]),
                       [[0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8], [0x9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF, 0x10]])

        # three frames needed
        self.assertEqual(canLink.segmentDatagramDataArray([0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF, 0x10, 0x11]),
                       [[0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8], [0x9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF, 0x10], [0x11]])


if __name__ == '__main__':
    unittest.main()
