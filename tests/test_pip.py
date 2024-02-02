import unittest

from openlcb.pip import PIP


class TestPipClass(unittest.TestCase):
    def setUpWithError(self):
        '''Put setup code here.
        This method is called before the invocation of
        each test method in the class.'''
        pass

    def testContainsSingle(self):
        result = PIP.setContentsFromInt(0x10_00_00_00)
        self.assertEqual(result, set([PIP.MEMORY_CONFIGURATION_PROTOCOL]))

    def testContainsMultiple(self):
        result = PIP.setContentsFromInt(0x10_10_00_00)
        self.assertEqual(
            result,
            set([PIP.MEMORY_CONFIGURATION_PROTOCOL,
                PIP.SIMPLE_NODE_IDENTIFICATION_PROTOCOL])
        )

    def testContainsFromRaw2(self):
        array = [0x10, 0x10]
        result = PIP.setContentsFromList(array)
        self.assertEqual(
            result,
            set([PIP.MEMORY_CONFIGURATION_PROTOCOL,
                PIP.SIMPLE_NODE_IDENTIFICATION_PROTOCOL])
        )

    def testContainsFromRaw4(self):
        array = [0x10, 0x10, 0, 0]
        result = PIP.setContentsFromList(array)
        self.assertEqual(
            result,
            set([PIP.MEMORY_CONFIGURATION_PROTOCOL,
                PIP.SIMPLE_NODE_IDENTIFICATION_PROTOCOL])
        )

    def testContentsNameUInt1(self):
        result = PIP.contentsNamesFromInt(0x10_00_00)
        self.assertEqual(result, ["Simple Node Identification Protocol"])

    def testContentsNameUSet(self):
        input = set([PIP.SIMPLE_NODE_IDENTIFICATION_PROTOCOL])
        result = PIP.contentsNamesFromList(input)
        self.assertEqual(result, ["Simple Node Identification Protocol"])


if __name__ == '__main__':
    unittest.main()
