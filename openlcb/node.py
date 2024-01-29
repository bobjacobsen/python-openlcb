'''
#
#  Node.swift
#
#  Created by Bob Jacobsen on 6/1/22.
#
#/ Central organizing point for information contained in a physical Node.
#/
#/  This is a class, not a struct, because an instance corresponds to an external object (the actual Node), so
#/  there's no semantic meaning to making multiple copies.
#/
#/  Concrete implementations may include a "node in this machine" and a "remote node elsewhere" a.k.a an image node.
#/
'''

from enum import Enum
from nodeid import *
from snip import *

class Node :
    
    def __init__(self, nodeID, snip=SNIP(), pipSet=set([]) ) :
        self.id = nodeID
        self.snip = snip
        self.pipSet = pipSet
        self.state = Node.State.Uninitialized
        self.events = None
    
    def __str__(self) :
        return "Node ("+str(self.id)+")"
        
    def name(self) :
        return self.snip.userProvidedNodeName

    class State(Enum) :
        Uninitialized = 1
        Initialized   = 2
    
    #/ Equality is defined on the NodeID only.
    def __eq__(lhs, rhs) :
        if rhs == None : return False
        return lhs.id == rhs.id

    def __hash__(self) :
        return hash(self.id)

    def __gt__(lhs, rhs) :
        return lhs.id.nodeId > rhs.id.nodeId
    def __lt__(lhs, rhs) :
        return lhs.id.nodeId < rhs.id.nodeId
        