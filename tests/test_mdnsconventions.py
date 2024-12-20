import os
import sys
import unittest

if __name__ == "__main__":
    TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
    REPO_DIR = os.path.dirname(TESTS_DIR)
    sys.path.insert(0, REPO_DIR)


from openlcb.tcplink.mdnsconventions import id_from_tcp_service_name


class TestConventions(unittest.TestCase):
    def test_id_from_tcp_service_name(self):
        self.assertIsNone(id_from_tcp_service_name("aaaaa.local."))
        self.assertEqual(id_from_tcp_service_name(
            "bobjacobsen_pythonopenlcb_02015700049C._openlcb-can._tcp.local."),
            "02.01.57.00.04.9C"
        )


if __name__ == '__main__':
    unittest.main()
