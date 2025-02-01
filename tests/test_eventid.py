import unittest

from openlcb.eventid import EventID


class TestEventIDClass(unittest.TestCase):

    def testInitString(self):
        eid = EventID("08.09.0A.0B.0C.0D.0E.0F")
        self.assertEqual(str(eid), "08.09.0A.0B.0C.0D.0E.0F")
        eid2 = EventID("FF.09.0A.0B.0C.0D.0E.0F")
        self.assertEqual(str(eid2), "FF.09.0A.0B.0C.0D.0E.0F")

        eid3 = EventID("FF.9.A.B.C.D.E.F")
        self.assertEqual(str(eid3), "FF.09.0A.0B.0C.0D.0E.0F")
        eid4 = EventID("A.B.C.D.E.F")
        self.assertEqual(str(eid4), "00.00.0A.0B.0C.0D.0E.0F")

        eid5 = EventID("08090A0B0C0D0E0F")
        self.assertEqual(str(eid5), "08.09.0A.0B.0C.0D.0E.0F")

    def testInitArray(self):
        array = bytearray([8, 9, 10, 11, 12, 13, 14, 15])
        eid = EventID(array)
        self.assertEqual(str(eid), "08.09.0A.0B.0C.0D.0E.0F")
        eid2 = EventID("FF.09.0A.0B.0C.0D.0E.0F")
        self.assertEqual(str(eid2), "FF.09.0A.0B.0C.0D.0E.0F")

    def testToArray(self):
        eid = EventID(0x0102030405060708)
        self.assertEqual(eid.toArray(),
                         bytearray([1, 2, 3, 4, 5, 6, 7, 8]))

    def testDescription(self):
        eid = EventID(0x08090A0B0C0D0E0F)
        self.assertEqual(str(eid), "08.09.0A.0B.0C.0D.0E.0F")

        eid2 = EventID(0xF8F9FAFBFCFDFEFF)
        self.assertEqual(str(eid2), "F8.F9.FA.FB.FC.FD.FE.FF")

    def testEquality(self):
        eid12 = EventID(12)
        eid12a = EventID(12)
        eid13 = EventID(13)
        self.assertEqual(eid12, eid12a, "same contents equal")
        self.assertNotEqual(eid12, eid13, "different contents not equal")


if __name__ == '__main__':
    unittest.main()
