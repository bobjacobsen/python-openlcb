'''
//
//  Message.swift
//
//  Created by Bob Jacobsen on 6/1/22.
//
/// Represents the basic message, with an MTI, source, destination? and data content.
'''
class Message : 
    
    # Message initialization
    # pass destination as None for global
    def __init__(self, mti, source, destination, data=[]) :
        self.mti = mti
        self.source = source
        self.destination = destination
        self.data = data
    
    def isGlobal(self) :
        return self.mti.value  & 0x0008 == 0
    
    def isAddressed(self) :
        return self.mti.value & 0x0008 != 0

    def __str__(self) :
        return "Message ("+self.mti.name+")"