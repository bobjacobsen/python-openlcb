import unittest

from openlcb.snip import SNIP


class TestSnipClass(unittest.TestCase):

    def testInitialValue(self):
        snip = SNIP()
        self.assertEqual(snip.hardwareVersion, "", "Not nil")

    def testGetString(self):
        s = SNIP()  # init to all zeros
        s.data = [0x41]*253
        s.data[4] = 0
        self.assertEqual(s.getString(1, 5), "AAA")

        s.data = [0x41]*253  # no trailing zero
        self.assertEqual(s.getString(1, 5), "AAAAA")

    def testLoadAndGetShort(self):
        s = SNIP() # init to all zeros
        s.data = [0x41]*253

        s.addData([4, 0x41, 0x42, 0x43, 0])  # version + "ABC"
        self.assertEqual(s.data[3], 0x43)

        s.addData([0x44, 0x45, 0x46, 0])  # DEF
        self.assertEqual(s.data[7], 0x46)

        s.addData([0x31, 0x45, 0x46, 0])  # 1EF
        s.addData([0x32, 0x45, 0x46, 0])
        s.addData([2])  # 2nd version string
        s.addData([0x33, 0x45, 0x46, 0])
        s.addData([0x34, 0x45, 0x46, 0])

        self.assertEqual(s.getStringN(0), "ABC", "get 0")
        self.assertEqual(s.getStringN(1), "DEF")
        self.assertEqual(s.getStringN(2), "1EF")
        self.assertEqual(s.getStringN(3), "2EF")
        self.assertEqual(s.getStringN(4), "3EF")
        self.assertEqual(s.getStringN(5), "4EF")

        self.assertEqual(s.manufacturerName, "ABC", "get mfg")
        self.assertEqual(s.modelName, "DEF")
        self.assertEqual(s.hardwareVersion, "1EF")
        self.assertEqual(s.softwareVersion, "2EF")
        self.assertEqual(s.userProvidedNodeName, "3EF")
        self.assertEqual(s.userProvidedDescription, "4EF")

    def testCharacterDecode(self):
        # This checks how we're converting strings to byte arrays
        str1 = "1234567890"

        first3Bytes = '{:.3}'.format(str1).encode('ASCII')
        self.assertEqual(len(first3Bytes), 3)
        self.assertEqual(first3Bytes[0], 0x31)

        first20Bytes = '{:.20}'.format(str1).encode('ASCII')
        self.assertEqual(first20Bytes[0], 0x31)

    def testLoadStrings(self):
        s = SNIP()  # init to all zeros

        s.manufacturerName = "ABC"
        s.modelName = "DEF"
        s.hardwareVersion = "1EF"
        s.softwareVersion = "2EF"
        s.userProvidedNodeName = "3EF"
        s.userProvidedDescription = "4EF"

        s.updateSnipDataFromStrings()

        self.assertEqual(s.getStringN(0), "ABC")
        self.assertEqual(s.getStringN(1), "DEF")
        self.assertEqual(s.getStringN(2), "1EF")
        self.assertEqual(s.getStringN(3), "2EF")
        self.assertEqual(s.getStringN(4), "3EF")
        self.assertEqual(s.getStringN(5), "4EF")

    def testReturnStrings(self):
        s = SNIP()  # init to all zeros

        s.manufacturerName = "ABC"
        s.modelName = "DEF"
        s.hardwareVersion = "1EF"
        s.softwareVersion = "2EF"
        s.userProvidedNodeName = "3EF"
        s.userProvidedDescription = "4EF"

        s.updateSnipDataFromStrings()

        result = s.returnStrings()

        self.assertEqual(result[0], 4)

        self.assertEqual(result[1], 0x41)
        self.assertEqual(result[2], 0x42)
        self.assertEqual(result[3], 0x43)
        self.assertEqual(result[4], 0)

        self.assertEqual(result[5], 0x44)
        self.assertEqual(result[6], 0x45)
        self.assertEqual(result[7], 0x46)
        self.assertEqual(result[8], 0)

        self.assertEqual(result[9], 0x31)
        self.assertEqual(result[10], 0x45)
        self.assertEqual(result[11], 0x46)
        self.assertEqual(result[12], 0)

        self.assertEqual(result[13], 0x32)
        self.assertEqual(result[14], 0x45)
        self.assertEqual(result[15], 0x46)
        self.assertEqual(result[16], 0)

        self.assertEqual(result[17], 2)

        self.assertEqual(result[18], 0x33)
        self.assertEqual(result[19], 0x45)
        self.assertEqual(result[20], 0x46)
        self.assertEqual(result[21], 0)

        self.assertEqual(result[22], 0x34)
        self.assertEqual(result[23], 0x45)
        self.assertEqual(result[24], 0x46)
        self.assertEqual(result[25], 0)

    def testName(self):
        s = SNIP()  # init to all zeros
        s.userProvidedNodeName = "test 123"
        s.updateSnipDataFromStrings()
        s.updateStringsFromSnipData()
        self.assertEqual(s.userProvidedNodeName, "test 123")

    def testConvenienceCtor(self):
        s = SNIP("mfgName", "model", "hVersion", "sVersion", "uName", "uDesc")

        self.assertEqual(s.manufacturerName, "mfgName")
        self.assertEqual(s.modelName, "model")
        self.assertEqual(s.hardwareVersion, "hVersion")
        self.assertEqual(s.softwareVersion, "sVersion")
        self.assertEqual(s.userProvidedNodeName, "uName")
        self.assertEqual(s.userProvidedDescription, "uDesc")


if __name__ == '__main__':
    unittest.main()
