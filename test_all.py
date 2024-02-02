import unittest

# WARNING is normal during testing, but ERROR is not
import logging
logging.basicConfig(level=logging.ERROR,
                    format='%(name)s %(levelname)s %(message)s')

from tests.test_eventid import *
from tests.test_nodeid import *
from tests.test_node import *

from tests.test_canframe import *

from tests.test_physicallayer import *
from tests.test_canphysicallayer import *
from tests.test_canphysicallayergridconnect import *

from tests.test_tcplink import *

from tests.test_mti import *
from tests.test_message import *

from tests.test_linklayer import *
from tests.test_canlink import *

from tests.test_datagramservice import *

from tests.test_memoryservice import *

from tests.test_snip import *
from tests.test_pip import *

from tests.test_processor import *

from tests.test_localnodeprocessor import *


if __name__ == '__main__':
    unittest.main()
