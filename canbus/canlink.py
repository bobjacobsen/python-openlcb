'''
based on CanLink.swift

Created by Bob Jacobsen on 6/1/22.


Handles link-layer formatting and unformatting for CAN-frame links.

Uses a ``CanPhysicalLayer`` implementation at the CanFrame layer.

This implementation handles one static Local Node and a variable number of
Remote Nodes.
 - An alias is allocated for the Local Node when the link comes up.
 - Aliases are tracked for the Remote Nodes, but not allocated here

 Multi-frame addressed messages are accumulated in parallel
'''

from canbus.canframe import CanFrame
# from canbus.canphysicallayer import CanPhysicalLayer
from openlcb.controlframe import ControlFrame
from openlcb.linklayer import LinkLayer
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.nodeid import NodeID

import logging
# from enum import Enum


class CanLink(LinkLayer):

    def __init__(self, localNodeID):  # a NodeID
        self.localAliasSeed = localNodeID.nodeId
        self.localAlias = self.createAlias12(self.localAliasSeed)
        self.localNodeID = localNodeID
        self.state = LinkLayer.State.Initial
        self.link = None
        self.aliasToNodeID = {}
        self.nodeIdToAlias = {}
        self.accumulator = {}
        self.nextInternallyAssignedNodeID = 1

    def linkPhysicalLayer(self, cpl):  # CanPhysicalLayer
        self.link = cpl
        cpl.registerFrameReceivedListener(self.receiveListener)

    def receiveListener(self, frame):  # CanFrame
        match self.decodeControlFrameFormat(frame):
            case ControlFrame.LinkUp:
                self.handleReceivedLinkUp(frame)
            case ControlFrame.LinkRestarted:
                self.handleReceivedLinkRestarted(frame)
            case ControlFrame.LinkCollision | ControlFrame.LinkError:
                logging.warning("Unexpected error report {:08X}"
                                "".format(frame.header))
            case ControlFrame.LinkDown:
                self.handleReceivedLinkDown(frame)
            case ControlFrame.CID:
                self.handleReceivedCID(frame)
            case ControlFrame.RID:
                self.handleReceivedRID(frame)
            case ControlFrame.AMD:
                self.handleReceivedAMD(frame)
            case ControlFrame.AME:
                self.handleReceivedAME(frame)
            case ControlFrame.AMR:
                self.handleReceivedAMR(frame)
            case (ControlFrame.EIR0 | ControlFrame.EIR1 | ControlFrame.EIR2,
                  ControlFrame.EIR3):
                pass   # ignored upon receipt
            case ControlFrame.Data:
                self.handleReceivedData(frame)
            case ControlFrame.UnknownFormat:
                logging.warning("Unexpected CAN header 0x{:08X}"
                                "".format(frame.header))

    def handleReceivedLinkUp(self, frame):  # CanFrame
        """Link started, update state, start process to create alias.
        LinkUp message will be sent when alias process completes.

        Args:
            frame (_type_): _description_
        """
        # start the alias allocation in Inhibited state
        self.state = LinkLayer.State.Inhibited
        self.defineAndReserveAlias()
        #    notify upper layers
        self.linkStateChange(self.state)

    def handleReceivedLinkRestarted(self, frame):  # CanFrame
        """Send a LinkRestarted message upstream.

        Args:
            frame (_type_): _description_
        """
        msg = Message(MTI.Link_Layer_Restarted, NodeID(0), None, [])
        self.fireListeners(msg)

    def defineAndReserveAlias(self):
        self.sendAliasAllocationSequence()

        # TODO: wait 200 msec before declaring ready to go (and doing
        # steps following the call here)

        # send AMD frame, go to Permitted state
        self.link.sendCanFrame(CanFrame(ControlFrame.AMD.value,
                                        self.localAlias,
                                        self.localNodeID.toArray()))
        self.state = LinkLayer.State.Permitted
        # add to map
        self.aliasToNodeID[self.localAlias] = self.localNodeID
        self.nodeIdToAlias[self.localNodeID] = self.localAlias
        #    send AME with no NodeID to get full alias map
        self.link.sendCanFrame(CanFrame(ControlFrame.AME.value,
                                        self.localAlias))

    #    TODO: (restart) Should this set inhibited every time? LinkUp not
    #    called on restart
    #    TODO: (restart) This is not called; there's no callback for it in
    #    Telnet library
    def handleReceivedLinkDown(self, frame):  # CanFrame
        """return to Inhibited state until link back up

        Args:
            frame (_type_): _description_
        """
        # NOTE: since no working link, not sending the AMR frame
        self.state = LinkLayer.State.Inhibited

        # print("***** received link down")
        # import traceback
        # traceback.print_stack()

        #    notify upper levels
        self.linkStateChange(self.state)

    def handleReceivedCID(self, frame):  # CanFrame
        #    Does this carry our alias?
        if (frame.header & 0xFFF) != self.localAlias:
            return  # no match
        #    send an RID in response
        self.link.sendCanFrame(CanFrame(ControlFrame.RID.value,
                                        self.localAlias))

    def handleReceivedRID(self, frame):  # CanFrame
        if (self.checkAndHandleAliasCollision(frame)):
            return

    def handleReceivedAMD(self, frame):  # CanFrame
        if (self.checkAndHandleAliasCollision(frame)):
            return
        #    This defines an alias, so store it
        nodeID = NodeID(frame.data)
        alias = frame.header & 0xFFF
        self.aliasToNodeID[alias] = nodeID
        self.nodeIdToAlias[nodeID] = alias

    def handleReceivedAME(self, frame):  # CanFrame
        if self.checkAndHandleAliasCollision(frame):
            return
        if self.state != LinkLayer.State.Permitted:
            return
        #    check node ID
        matchNodeID = self.localNodeID
        if (len(frame.data) >= 6):
            matchNodeID = NodeID(frame.data)

        if (self.localNodeID == matchNodeID):
            #    matched, send RID
            returnFrame = CanFrame(ControlFrame.AMD.value, self.localAlias,
                                   self.localNodeID.toArray())
            self.link.sendCanFrame(returnFrame)

    def handleReceivedAMR(self, frame):  # CanFrame
        if (self.checkAndHandleAliasCollision(frame)):
            return
        #    Alias Map Reset - drop from maps
        nodeID = NodeID(frame.data)
        alias = frame.header & 0xFFF
        try:
            del self.aliasToNodeID[alias]
            del self.nodeIdToAlias[nodeID]
        except:
            pass

    def handleReceivedData(self, frame):  # CanFrame
        if self.checkAndHandleAliasCollision(frame):
            return
        #    get proper MTI
        mti = self.canHeaderToFullFormat(frame)
        sourceID = NodeID(0)
        try:
            mapped = self.aliasToNodeID[frame.header & 0xFFF]
            sourceID = mapped
        except:
            #    special case for JMRI before 5.1.5 which sends
            #    VerifiedNodeID but not AMD
            if mti == MTI.Verified_NodeID:
                sourceID = NodeID(frame.data)
                logging.info("Verified_NodeID from unknown source alias: {},"
                             " continue with observed ID {}"
                             "".format(frame, sourceID))
            else:
                sourceID = NodeID(self.nextInternallyAssignedNodeID)
                self.nextInternallyAssignedNodeID += 1
                logging.warning("message from unknown source alias: {},"
                                " continue with created ID {}"
                                "".format(frame, sourceID))

            #    register that internally-generated nodeID-alias association
            self.aliasToNodeID[frame.header & 0xFFF] = sourceID
            self.nodeIdToAlias[sourceID] = frame.header & 0xFFF

        destID = NodeID(0)
        #    handle destination for addressed messages
        dgCode = frame.header & 0x00F_000_000
        if (frame.header & 0x008_000 != 0
                or (dgCode >= 0x00A_000_000 and dgCode <= 0x00F_000_000)):
            #    Addressed bit is active 1
            #    decoder regular addressed message from Datagram
            if (dgCode >= 0x00A_000_000 and dgCode <= 0x00F_000_000):
                #    datagram case

                destAlias = (frame.header & 0x00_FFF_000) >> 12
                mapped = self.aliasToNodeID[destAlias]
                if mapped is not None:
                    destID = mapped
                else:
                    destID = NodeID(self.nextInternallyAssignedNodeID)
                    logging.warning("message from unknown dest alias: {},"
                                    " continue with {}", format(frame, destID))
                    #    register that internally-generated nodeID-alias
                    #    association
                    self.aliasToNodeID[destAlias] = destID
                    self.nodeIdToAlias[destID] = destAlias

                #    check for start and end bits
                key = CanLink.AccumKey(mti, sourceID, destID)
                if dgCode == 0x00A_000_000 or dgCode == 0x00B_000_000:
                    #    start of message, create the entry in the accumulator
                    self.accumulator[key] = []
                else:
                    # not start frame
                    # check for never properly started, this is an error
                    if key not in self.accumulator:
                        #    have not-start frame, but never started
                        logging.warning(
                            "Dropping non-start datagram frame"
                            " without accumulation started:"
                            " {}".format(frame)
                            # TODO: ^ more necessary to show same output
                            #   as Swift? Formerly:
                            #   " \(frame, privacy: .public)"
                        )
                        return  # early return to stop processing of this frame

                # add this data
                if len(frame.data) > 0:
                    self.accumulator[key].extend(frame.data)

                if dgCode == 0x00A_000_000 or dgCode == 0x00D_000_000:
                    #    is end, ship and remove accumulation
                    msg = Message(mti, sourceID, destID, self.accumulator[key])
                    self.fireListeners(msg)

                    #    remove accumulution
                    self.accumulator[key] = None
            else:
                #    addressed message case
                destAlias = 0
                if (len(frame.data) > 0):
                    destAlias |= (frame.data[0] & 0x0F) << 8  # rm f bits
                if (len(frame.data) > 1):
                    destAlias |= (frame.data[1] & 0xFF)
                try:
                    mapped = self.aliasToNodeID[destAlias]
                    destID = mapped
                except:
                    destID = NodeID(self.nextInternallyAssignedNodeID)
                    logging.warning("message from unknown dest alias:"
                                    " 0x{:04X}, continue with 0x{}"
                                    "".format(destAlias, destID))
                    #    register that internally-generated nodeID-alias
                    #    association
                    self.aliasToNodeID[destAlias] = destID
                    self.nodeIdToAlias[destID] = destAlias

                # check for start and end bits
                key = CanLink.AccumKey(mti, sourceID, destID)
                if (frame.data[0] & 0x20 == 0):
                    #    is start, create the entry in the accumulator
                    self.accumulator[key] = []
                else:
                    # not start frame
                    # check for first bit set never seen
                    if key not in self.accumulator:
                        #    have not-start frame, but never started
                        logging.warning("Dropping non-start frame without"
                                        " accumulation started: {}"
                                        "".format(frame))
                        return  # early return to stop processing of this grame

                #    add this data
                if len(frame.data) > 2:
                    for byte in frame.data[2:]:  # through end of array
                        self.accumulator[key].append(byte)

                if frame.data[0] & 0x10 == 0:
                    # is end, ship and remove accumulation
                    msg = Message(mti, sourceID, destID, self.accumulator[key])
                    self.fireListeners(msg)

                    # remove accumulution
                    self.accumulator[key] = None

            # end addressed message case

        else:
            # forward global message
            msg = Message(mti, sourceID, destID, frame.data)
            self.fireListeners(msg)

    def sendMessage(self, msg):
        #    special case for datagram
        if msg.mti == MTI.Datagram:
            header = 0x10_000_000
            #    datagram headers are
            #             1Adddsss - one frame
            #             1Bdddsss - first frame
            #             1Cdddsss - middle frame
            #             1Ddddsss - last frame
            try:
                sssAlias = self.nodeIdToAlias[msg.source]
                header |= ((sssAlias) & 0xFFF)
            except:
                logging.warning(
                    "Did not know source = {} on datagram send"
                    "".format(msg.source)
                )

            try:
                dddAlias = self.nodeIdToAlias[msg.destination]
                header |= ((dddAlias) & 0xFFF) << 12
            except:
                logging.warning(
                    "Did not know destination = {} on datagram send"
                    "".format(msg.source)
                )

            if len(msg.data) <= 8:
                #    single frame
                header |= 0x0A_000_000
                frame = CanFrame(header, msg.data)
                self.link.sendCanFrame(frame)
            else:
                #    multi-frame datagram
                dataSegments = self.segmentDatagramDataArray(msg.data)
                #    send the first one
                frame = CanFrame(header | 0x0B_000_000, dataSegments[0])
                self.link.sendCanFrame(frame)
                #    send middles
                if len(dataSegments) >= 3:
                    for index in range(1, len(dataSegments) - 2 + 1):
                        # upper limit leaves one
                        frame = CanFrame(header | 0x0C_000_000,
                                         dataSegments[index])
                        self.link.sendCanFrame(frame)

                # send last one
                frame = CanFrame(
                    header | 0x0D_000_000,
                    dataSegments[len(dataSegments) - 1]
                )
                self.link.sendCanFrame(frame)
        else:
            #    all non-datagram cases
            #    Remap the mti
            header = 0x19_000_000 | ((msg.mti.value & 0xFFF) << 12)

            alias = self.nodeIdToAlias[msg.source]
            if alias is not None:  # might not know it if error
                header |= (alias & 0xFFF)
            else:
                logging.warning("Did not know source = {} on message send"
                                "".format(msg.source))

            # Is a destination address needed? Could be long message
            if msg.isAddressed():
                destt = msg.destination
                if destt is None:
                    destt = NodeID(0)
                alias = self.nodeIdToAlias[destt]
                if alias is not None:  # might not know it?
                    #    address and have alias, break up data
                    dataSegments = self.segmentAddressedDataArray(alias,
                                                                  msg.data)
                    for content in dataSegments:
                        #    send the resulting frame
                        frame = CanFrame(header, content)
                        self.link.sendCanFrame(frame)
                else:
                    logging.warning("Don't know alias for destination = {}"
                                    "".format(msg.destination or NodeID(0)))
            else:
                #    global still can hold data; assume length is correct by
                #    protocol send the resulting frame
                frame = CanFrame(header, msg.data)
                self.link.sendCanFrame(frame)

    def segmentDatagramDataArray(self, data):
        """Segment data into zero or more arrays
        of no more than 8 bytes for datagram.

        Args:
            data (_type_): _description_

        Returns:
            _type_: _description_
        """
        nSegments = (len(data)+7) // 8
        # ^ the +7 is since integer division takes the floor value
        if nSegments == 0:
            return [[]]

        if nSegments == 1:
            return [data]

        #    multiple frames
        retval = []
        for i in range(0, nSegments-2+1):  # first enty of 2 has full data
            nextEntry = (data[i*8:i*8+7+1]).copy()
            retval.append(nextEntry)

        #    add the last
        lastEntry = (data[8*(nSegments-1):]).copy()
        retval.append(lastEntry)

        return retval

    def segmentAddressedDataArray(self, alias, data):
        '''Segment data into zero or more arrays
        of no more than 8 bytes, with the alias at the start of each,
        for addressed non-datagram messages.

        Args:
            alias (int): _description_
            data (_type_): _description_

        Returns:
            _type_: _description_
        '''
        part0 = (alias >> 8) & 0xF
        part1 = alias & 0xFF
        nSegments = (len(data)+5) // 6  # the +5 is since integer division
        #   takes the floor value
        if nSegments == 0:
            return [[part0, part1]]
        if nSegments == 1:
            return [[part0, part1]+data]

        #    multiple frames
        retval = []
        for i in range(0, nSegments-2+1):  # first enty of 2 has full data
            nextEntry = [part0 | 0x30, part1]+(data[i*6:i*6+5+1]).copy()
            retval.append(nextEntry)

        #    add the last
        lastEntry = [part0 | 0x20, part1]+(data[6*(nSegments-1):]).copy()
        retval.append(lastEntry)
        #    mark first (last already done above)
        retval[0][0] &= ~0x20

        return retval

    #    MARK: common code
    def checkAndHandleAliasCollision(self, frame):
        if self.state != LinkLayer.State.Permitted:
            return False
        receivedAlias = frame.header & 0x0000_FFF
        abort = (receivedAlias == self.localAlias)
        if abort:
            #    Collision!
            logging.warning("alias collision in {}, we restart with AMR"
                            " and attempt to get new alias".format(frame))
            self.link.sendCanFrame(CanFrame(ControlFrame.AMR.value,
                                            self.localAlias,
                                            self.localNodeID.toArray()))
            #    Standard 6.2.5
            self.state = LinkLayer.State.Inhibited
            #    attempt to get a new alias and go back to .Permitted
            self.localAliasSeed = self.incrementAlias48(self.localAliasSeed)
            self.localAlias = self.createAlias12(self.localAliasSeed)
            self.defineAndReserveAlias()

        return abort

    def sendAliasAllocationSequence(self):
        '''Send the alias allocation sequence'''
        self.link.sendCanFrame(CanFrame(7, self.localNodeID, self.localAlias))
        self.link.sendCanFrame(CanFrame(6, self.localNodeID, self.localAlias))
        self.link.sendCanFrame(CanFrame(5, self.localNodeID, self.localAlias))
        self.link.sendCanFrame(CanFrame(4, self.localNodeID, self.localAlias))
        self.link.sendCanFrame(CanFrame(ControlFrame.RID.value,
                                        self.localAlias))

    #    Implements the OpenLCB preferred alias
    #     generation mechanism:  a 48-bit computation
    #     of x(i+1) = (2^9+1) x(i) + c
    #     where c = 29,741,096,258,473 or 0x1B0CA37A4BA9
    def incrementAlias48(self, oldAlias):
        newProduct = (oldAlias << 9) + oldAlias + (0x1B0CA37A4BA9)
        maskedProduct = newProduct & 0xFFFF_FFFF_FFFF
        return maskedProduct

    #    Form 12 bit alias from 48-bit random number
    def createAlias12(self, rnd):
        part1 = (rnd >> 36) & 0x0FFF
        part2 = (rnd >> 24) & 0x0FFF
        part3 = (rnd >> 12) & 0x0FFF
        part4 = (rnd) & 0x0FFF

        if (part1 ^ part2 ^ part3 ^ part4) != 0:
            return (part1 ^ part2 ^ part3 ^ part4)
        else:
            #    zero is not a valid alias, so provide a non-zero value
            if ((part1+part2+part3+part4) & 0xFF) != 0:
                return ((part1+part2+part3+part4) & 0xFF)
            else:
                return 0xAEF  # Why'd you say Burma?

    def decodeControlFrameFormat(self, frame):
        if (frame.header & 0x0800_0000) == 0x0800_0000:
            # data case; not checking leading 1 bit
            return ControlFrame.Data
        elif (frame.header & 0x4_000_000) != 0:  # CID case
            return ControlFrame.CID
        else:
            try:
                retval = ControlFrame((frame.header >> 12) & 0x2FFFF)
                return retval  # top 1 bit for out-of-band messages
            except:
                logging.warning("Could not decode header 0x{:08X}"
                                "".format(frame.header))
                return ControlFrame.UnknownFormat

    def canHeaderToFullFormat(self, frame):
        '''Returns a full 16-bit MTI from the full 29 bits of a CAN header'''
        frameType = (frame.header >> 24) & 0x7
        canMTI = ((frame.header >> 12) & 0xFFF)

        if frameType == 1:
            okMTI = MTI(canMTI)
            if okMTI is not None:
                return okMTI
            else:
                logging.warning("unhandled canMTI: {}, marked Unknown"
                                "".format(frame))
                return MTI.Unknown

        elif (frameType >= 2 and 5 >= frameType):
            #    datagram type - we don't address the subtypes here
            return MTI.Datagram
        else:
            #    not handling reserver and stream type except to log
            logging.warning("unhandled canMTI: {}, marked Unknown"
                            "".format(frame))
            return MTI.Unknown

    class AccumKey:
        '''Class that holds the ID for accumulating a multi-part message:
        - MTI
        - Source
        - Destination

        Together these uniquely identify a stream of frames that need to
        be assembled into a message
        '''
        def __init__(self, mti, source, dest):
            self.mti = mti
            self.source = source
            self.dest = dest

        def __hash__(self):
            return hash(self.mti)+hash(self.source)+hash(self.dest)

        def __eq__(self, other):
            if self.mti != other.mti:
                return False
            if self.source != other.source:
                return False
            if self.dest != other.dest:
                return False
            return True
