'''
based on Message.swift
Created by Bob Jacobsen on 6/1/22.
'''


class Message:
    """basic message, with an MTI, source, destination? and data content

    Args:
        mti (_type_): _description_
        source (_type_): _description_
        destination (_type_): Set to None for global.
        data (list, optional): _description_. Defaults to [].

    Returns:
        _type_: _description_
    """

    def __init__(self, mti, source, destination, data=[]):
        # For args, see class docstring.
        self.mti = mti
        self.source = source
        self.destination = destination
        self.data = data

    def isGlobal(self):
        return self.mti.value & 0x0008 == 0

    def isAddressed(self):
        return self.mti.value & 0x0008 != 0

    def __str__(self):
        return "Message ("+self.mti.name+")"

    def __eq__(lhs, rhs):
        if rhs is None:
            return False
        if rhs.mti != lhs.mti:
            return False
        if rhs.source != lhs.source:
            return False
        if rhs.destination != lhs.destination:
            return False
        if rhs.data != lhs.data:
            return False
        return True

    def __hash__(self) :
        return self.mti.__hash__() + self.source.__hash__()