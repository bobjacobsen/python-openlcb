import unittest

from openlcb.localeventstore import LocalEventStore

from openlcb.eventid import EventID


class TestLocalEventStorelass(unittest.TestCase):

    def testConsumes(self) :
        store = LocalEventStore()

        store.consumes(EventID(2))
        self.assertTrue(store.isConsumed(EventID(2)))
        self.assertFalse(store.isConsumed(EventID(3)))

    def testProduces(self) :
        store = LocalEventStore()

        store.produces(EventID(4))
        self.assertTrue(store.isProduced(EventID(4)))
        self.assertFalse(store.isProduced(EventID(5)))


if __name__ == '__main__':
    unittest.main()
