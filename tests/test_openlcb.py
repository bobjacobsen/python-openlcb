import os
import sys
import unittest

if __name__ == "__main__":
    TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
    REPO_DIR = os.path.dirname(TESTS_DIR)
    sys.path.insert(0, REPO_DIR)

from openlcb import only_hex_pairs


class TestConventions(unittest.TestCase):
    def test_only_hex_pairs(self):
        self.assertTrue(only_hex_pairs("02015700049C"))
        self.assertTrue(only_hex_pairs("02015700049c"))
        self.assertTrue(only_hex_pairs("02"))

        self.assertFalse(only_hex_pairs("02.01.57.00.04.9C"))  # contains separator
        # ^ For the positive test (& allowing elements not zero-padded) see test_conventions.py
        self.assertFalse(only_hex_pairs("02015700049C."))  # contains end character
        self.assertFalse(only_hex_pairs("0"))  # not a full pair
        self.assertFalse(only_hex_pairs("_02015700049C"))  # contains start character
        self.assertFalse(only_hex_pairs("org_product_02015700049C"))  # service name not split



if __name__ == '__main__':
    unittest.main()
