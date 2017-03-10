# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces import IPloneSiteRoot
from bda.plone.orders.common import acquire_vendor_or_shop_root
from bda.plone.orders.interfaces import IVendor
from bda.plone.orders.tests import Orders_INTEGRATION_TESTING
from bda.plone.orders.tests import set_browserlayer
from zope.interface import alsoProvides
import unittest


class TestOrders(unittest.TestCase):
    layer = Orders_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        set_browserlayer(self.request)


class DummyContext(dict):
    __parent__ = None

    def __nonzero__(self):
        return True

    def __setitem__(self, key, val):
        assert(isinstance(val, DummyContext))
        val.__parent__ = self
        super(DummyContext, self).__setitem__(key, val)


class TestOrdersUnit(unittest.TestCase):

    def setUp(self):
        root = DummyContext()
        root['sub1'] = DummyContext()
        root['sub1']['subsub1'] = DummyContext()
        root['sub2'] = DummyContext()

        alsoProvides(root, IPloneSiteRoot)
        alsoProvides(root['sub1'], IVendor)
        self.root = root

    def test_acquire_vendor_or_shop_root(self):
        root = self.root
        self.assertEqual(
            acquire_vendor_or_shop_root(root['sub1']['subsub1']),
            root['sub1']
        )
        self.assertEqual(acquire_vendor_or_shop_root(root['sub2']), root)
