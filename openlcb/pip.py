'''
based on PIP.swift
Created by Bob Jacobsen on 6/1/22.

Defines the various protocol bits as a enum, and
provides a routine for converting a numeric value to a set of enum constants.
'''

from enum import Enum


class PIP(Enum):
    """Coded as a 32-bit values
    instead of the 24-bit values in the standard to give expansion room.
    """
    SIMPLE_PROTOCOL                        = 0x80_00_00_00
    DATAGRAM_PROTOCOL                      = 0x40_00_00_00
    STREAM_PROTOCOL                        = 0x20_00_00_00
    MEMORY_CONFIGURATION_PROTOCOL          = 0x10_00_00_00
    RESERVATION_PROTOCOL                   = 0x08_00_00_00
    EVENT_EXCHANGE_PROTOCOL                = 0x04_00_00_00
    IDENTIFICATION_PROTOCOL                = 0x02_00_00_00
    TEACH_LEARN_PROTOCOL                   = 0x01_00_00_00
    REMOTE_BUTTON_PROTOCOL                 = 0x00_80_00_00
    ADCDI_PROTOCOL                         = 0x00_40_00_00
    DISPLAY_PROTOCOL                       = 0x00_20_00_00
    SIMPLE_NODE_IDENTIFICATION_PROTOCOL    = 0x00_10_00_00
    CONFIGURATION_DESCRIPTION_INFORMATION  = 0x00_08_00_00
    TRAIN_CONTROL_PROTOCOL                 = 0x00_04_00_00
    FUNCTION_DESCRIPTION_INFORMATION       = 0x00_02_00_00
    DCC_COMMAND_STATION_PROTOCOL           = 0x00_01_00_00
    SIMPLE_TRAIN_NODE_INFO_PROTOCOL        = 0x00_00_80_00
    FUNCTION_CONFIGURATION                 = 0x00_00_40_00
    FIRMWARE_UPGRADE_PROTOCOL              = 0x00_00_20_00
    FIRMWARE_ACTIVE                        = 0x00_00_10_00

    # get a list of all enum entries
    def list():
        return list(map(lambda c: c, PIP))

    # return an array of strings found in an int value
    def contentsNamesFromInt(contents):
        retval = []
        for pip in PIP.list():
            if (pip.value & contents == pip.value):
                retval.append(pip.name.replace("_", " ").title())
        return retval

    # return an array of strings for all values included in a collection
    def contentsNamesFromList(contents):
        retval = []
        for pip in contents:
            retval.append(pip.name.replace("_", " ").title())
        return retval

    def setContentsFromInt(input):
        """Get a set of contents from a single numeric input

        Args:
            input (_type_): _description_

        Returns:
            set: _description_
        """
        retVal = []
        for val in PIP.list():
            if (val.value & input != 0):
                retVal.append(val)
        return set(retVal)

    def setContentsFromList(raw):
        """set contents from a list of numeric inputs

        Args:
            raw (_type_): _description_

        Returns:
            _type_: _description_
        """
        data = 0
        if (len(raw) > 0):
            data |= ((raw[0]) << 24)
        if (len(raw) > 1):
            data |= ((raw[1]) << 16)
        if (len(raw) > 2):
            data |= ((raw[2]) << 8)
        if (len(raw) > 3):
            data |= ((raw[3]))
        return PIP.setContentsFromInt(data)
