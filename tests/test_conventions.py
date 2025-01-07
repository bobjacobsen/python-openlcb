import os
import sys
import unittest

from logging import getLogger

logger = getLogger(__name__)


if __name__ == "__main__":
    # Allow importing repo copy of openlcb if running tests from repo manually.
    TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
    REPO_DIR = os.path.dirname(TESTS_DIR)
    if os.path.isfile(os.path.join(REPO_DIR, "openlcb", "__init__.py")):
        sys.path.insert(0, REPO_DIR)
    else:
        logger.warning(
            "Reverting to installed copy if present (or imports will fail),"
            " since test running from repo but could not find openlcb in {}."
            .format(repr(REPO_DIR)))


from openlcb.conventions import (  # noqa: E402
    dotted_lcc_id_to_hex,
    is_dotted_lcc_id,
    is_hex_lcc_id,
    hex_to_dotted_lcc_id,
)


class TestConventions(unittest.TestCase):
    """Cover conventions.py
    (is_hex_lcc_id, dotted_lcc_id_to_hex, and is_dotted_lcc_id
    cover validate_lcc_id other than checking which validation error
    occurred)
    """

    def test_is_hex_lcc_id(self):
        self.assertTrue(is_hex_lcc_id("02015700049C"))
        self.assertTrue(is_hex_lcc_id("02015700049c"))

        self.assertFalse(is_hex_lcc_id("02"))  # only_hex_pairs yet too short
        self.assertFalse(is_hex_lcc_id("2.1.57.0.4.9C"))  # not converted
        self.assertFalse(is_hex_lcc_id("02.01.57.00.04.9C"))  # not converted
        self.assertFalse(is_hex_lcc_id("02015700049C."))
        self.assertFalse(is_hex_lcc_id("0"))
        self.assertFalse(is_hex_lcc_id("_02015700049C"))  # contains start character
        self.assertFalse(is_hex_lcc_id("org_product_02015700049C"))  # service name not split

    def test_dotted_lcc_id_to_hex(self):
        self.assertEqual(dotted_lcc_id_to_hex("2.1.57.0.4.9C"),
                         "02015700049C")
        self.assertEqual(dotted_lcc_id_to_hex("02.01.57.00.04.9C"),
                         "02015700049C")
        self.assertEqual(dotted_lcc_id_to_hex("02.01.57.00.04.9c"),
                         "02015700049C")  # converted to uppercase OK

        self.assertNotEqual(dotted_lcc_id_to_hex("02.01.57.00.04.9c"),
                            "02015700049c")  # function should convert to uppercase
        self.assertIsNone(dotted_lcc_id_to_hex("02015700049C"))
        self.assertIsNone(dotted_lcc_id_to_hex("02015700049c"))
        self.assertIsNone(dotted_lcc_id_to_hex("02"))  # only_hex_pairs yet too short
        self.assertIsNone(dotted_lcc_id_to_hex("02015700049C."))
        self.assertIsNone(dotted_lcc_id_to_hex("0"))
        self.assertIsNone(dotted_lcc_id_to_hex("_02015700049C"))  # contains start character
        self.assertIsNone(dotted_lcc_id_to_hex("org_product_02015700049C"))  # service name not split

    def test_is_dotted_lcc_id(self):
        self.assertTrue(is_dotted_lcc_id("02.01.57.00.04.9C"))
        self.assertTrue(is_dotted_lcc_id("2.01.57.00.04.9C"))
        self.assertTrue(is_dotted_lcc_id("2.1.57.0.4.9C"))
        self.assertTrue(is_dotted_lcc_id("2.1.57.0.4.9c"))

        self.assertFalse(is_dotted_lcc_id("02.01.57.00.04.9G"))  # G is not hex
        self.assertFalse(is_dotted_lcc_id(".01.57.00.04.9C"))  # empty pair
        self.assertFalse(is_dotted_lcc_id("01.57.00.04.9C"))  # only 5 pairs
        self.assertFalse(is_dotted_lcc_id("02015700049C"))

    def test_hex_to_dotted_lcc_id(self):
        # NOTE: No case conversion occurs in this direction,
        #   so that doesn't need to be checked.
        self.assertEqual(hex_to_dotted_lcc_id("02015700049C"),
                         "02.01.57.00.04.9C")

    def test_hex_to_dotted_lcc_id_fail(self):
        exception = None
        try:
            _ = hex_to_dotted_lcc_id("2015700049C")
        except ValueError as ex:
            exception = ex
        self.assertIsInstance(exception, ValueError)


if __name__ == '__main__':
    unittest.main()
