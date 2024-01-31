'''
based on EventID.swift

Created by Bob Jacobsen on 6/1/22.

Represents an 8-byte event ID.

Provides conversion to and from Ints and Strings in standard form.
'''


class EventID:
    def __str__(self):
        '''Display in standard format'''
        c = self.toArray()
        return ("{:02X}.{:02X}.{:02X}.{:02X}.{:02X}.{:02X}.{:02X}.{:02X}"
                "".format(c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7]))

    # Convert an integer, list, NodeID or string to a NodeID
    def __init__(self, data):
        if isinstance(data, int):  # create from an integer value
            self.eventId = data
        elif isinstance(data, str):  # need to allow for 1 digit numbers
            parts = data.split(".")
            result = 0
            for part in parts:
                result = result*0x100+int(part, 16)
            self.eventId = result
        elif isinstance(data, EventID):
            self.eventId = data.nodeId
        elif isinstance(data, list):
            self.eventId = 0
            if (len(data) > 0):
                self.eventId |= (data[0] & 0xFF) << 56
            if (len(data) > 1):
                self.eventId |= (data[1] & 0xFF) << 48
            if (len(data) > 2):
                self.eventId |= (data[2] & 0xFF) << 40
            if (len(data) > 3):
                self.eventId |= (data[3] & 0xFF) << 32
            if (len(data) > 4):
                self.eventId |= (data[4] & 0xFF) << 24
            if (len(data) > 5):
                self.eventId |= (data[5] & 0xFF) << 16
            if (len(data) > 6):
                self.eventId |= (data[6] & 0xFF) << 8
            if (len(data) > 7):
                self.eventId |= (data[7] & 0xFF)
        else:
            print("invalid data type to nodeid constructor", data)

    def toArray(self):
        return [
            (self.eventId >> 56) & 0xFF,
            (self.eventId >> 48) & 0xFF,
            (self.eventId >> 40) & 0xFF,
            (self.eventId >> 32) & 0xFF,
            (self.eventId >> 24) & 0xFF,
            (self.eventId >> 16) & 0xFF,
            (self.eventId >> 8) & 0xFF,
            (self.eventId) & 0xFF
        ]

    def __eq__(self, other):
        if self.eventId != other.eventId:
            return False
        return True

    def __hash__(self):
        return hash(self.eventId)
