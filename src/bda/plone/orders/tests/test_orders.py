from bda.plone.orders.tests import Orders_INTEGRATION_TESTING
from bda.plone.orders.tests import set_browserlayer

import unittest2 as unittest


class TestOrders(unittest.TestCase):
    layer = Orders_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        set_browserlayer(self.request)

    def test_foo(self):
        self.assertEquals(1, 1)
