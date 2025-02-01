import os
import sys
import unittest

if __name__ == "__main__":
    TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
    REPO_DIR = os.path.dirname(TESTS_DIR)
    sys.path.insert(0, REPO_DIR)

from openlcb import (
    emit_cast,
    list_type_names,
    only_hex_pairs,
)


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

    def test_list_type_names(self):
        self.assertEqual(list_type_names({"a": 1, "b": "B"}),
                         ['a: int', 'b: str'])
        self.assertEqual(list_type_names([1, "b"]), ['int', 'str'])

    def test_list_type_names_fail(self):
        # These types make no sense to use
        #   (Use emit_cast instead for non-collections
        #   or to debug collections as one string)
        with self.assertRaises(TypeError):
            list_type_names("hello")

        with self.assertRaises(TypeError):
            list_type_names(b"\x00")  # bytes

        with self.assertRaises(TypeError):
            list_type_names(bytearray("hello".encode("utf-8")))

        with self.assertRaises(TypeError):
            list_type_names(1)

    def test_emit_cast(self):
        self.assertEqual(emit_cast(1), "int(1)")


if __name__ == '__main__':
    unittest.main()
