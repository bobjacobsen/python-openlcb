'''
//
//  CanPhysicalLayerGridConnect.swift
//
//
//  Created by Bob Jacobsen on 6/14/22.
//
/// Provide a CanPhysicalLayer for GridConnect format strings.
///
///
/// Works with frames like
///  -      :X19490365N;
///  -      :X19170365N020112FE056C;
'''

from canbus.canphysicallayer import CanPhysicalLayer

class CanPhysicalLayerGridConnect(CanPhysicalLayer) :

    def __init__( self, callback) :
        CanPhysicalLayer.__init__(self)
        self.canSendCallback = callback
        self.inboundBuffer = []

    def setCallBack(self, callback ) :
        self.canSendCallback = callback

    def sendCanFrame(self, frame) :
        output  = ":X{:08X}N".format(frame.header)
        for byte in frame.data :
            output += "{:02X}".format(byte)
        output += ";\n"
        self.canSendCallback(output)


    # Receive a string from the outside link to be parsed
    def receiveString(self, string) :
        self.receiveChars(string.encode("ASCII"))

    # Provide characters from the outside link to be parsed
    def receiveChars(self, data) :
        self.inboundBuffer += data
        lastByte = 0
        if 0x3B in self.inboundBuffer : #  ';' ends message so we have at least one (CR/LF not required)
            # found end, now find start of that same message, earlier in buffer
            for index in range(0, len(self.inboundBuffer)) :
                outData = []
                if not 0x3B in self.inboundBuffer[index:] : break
                if self.inboundBuffer[index] == 0x3A : # ':' starts message
                    # now start to accumulate data from entire message
                    header = 0
                    for offset in range(2,9+1) :
                        nextChar = (self.inboundBuffer[index+offset])
                        nextByte = (nextChar & 0xF)+9 if nextChar > 0x39 else nextChar & 0xF
                        header = (header<<4)+nextByte
                    # offset 10 is N
                    # offset 11 might be data, might be ;
                    lastByte = index+11
                    for dataItem in range(0,8) :
                        if self.inboundBuffer[index+11+2*dataItem] == 0x3B : break
                        # two characters are data
                        byte1 = self.inboundBuffer[index+11+2*dataItem]
                        part1 = (byte1 & 0xF)+9 if byte1 > 0x39 else byte1 & 0xF
                        byte2 = self.inboundBuffer[index+11+2*dataItem+1]
                        part2 = (byte2 & 0xF)+9  if byte2 > 0x39 else byte2 & 0xF
                        outData += [part1<<4 | part2]
                        lastByte += 2
                    # lastByte is index of ; in this message

                    cf = CanFrame(header, outData)
                    self.fireListeners(cf)

            # shorten buffer by removing the processed message
            self.inboundBuffer = self.inboundBuffer[lastByte:]

