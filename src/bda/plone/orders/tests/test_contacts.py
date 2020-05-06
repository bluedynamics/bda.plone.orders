# -*- coding: utf-8 -*-
from bda.plone.orders.tests import Orders_INTEGRATION_TESTING
from bda.plone.orders.tests import set_browserlayer

import unittest


class TestContacts(unittest.TestCase):
    layer = Orders_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        set_browserlayer(self.request)

    def test_next_contact_id(self):
        from bda.plone.orders import contacts

        soup = contacts.get_contacts_soup()
        contacts.CID_GENERATION["min"] = 10
        contacts.CID_GENERATION["min"] = 12
        self.assertTrue(10 <= contacts.next_contact_id(soup) <= 12)
