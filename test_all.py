import unittest

# WARNING is normal during testing, but ERROR is not
import logging
logging.basicConfig(level=logging.ERROR, format='%(name)s %(levelname)s %(message)s')

from eventid_test import *
from nodeid_test import *
from node_test import *

from canframe_test import *

from physicallayer_test import *
from canphysicallayer_test import *
from canphysicallayergridconnect_test import *

from mti_test import *
from message_test import *

from linklayer_test import *
from canlink_test import *

from datagramservice_test import *

from memoryservice_test import *

from snip_test import *
from pip_test import *

from processor_test import *

from localnodeprocessor_test import *

if __name__ == '__main__':
    unittest.main()
