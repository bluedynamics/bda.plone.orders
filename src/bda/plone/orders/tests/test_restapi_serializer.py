# -*- coding: utf-8 -*-
from bda.plone.orders.tests import Orders_INTEGRATION_TESTING
from bda.plone.orders.tests import set_browserlayer
from decimal import Decimal
from plone.restapi.interfaces import ISerializeToJson
from zope.component import getMultiAdapter

import unittest


class TestBookingSerializer(unittest.TestCase):
    layer = Orders_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        set_browserlayer(self.request)

    def _serializer(self, obj):
        serializer = getMultiAdapter((obj, self.request), ISerializeToJson)
        return serializer

    def _create_booking(self):
        from node.ext.zodb import OOBTNode
        raw_booking = OOBTNode()
        raw_booking.attrs['uid'] = "Unique-Id-001"
        raw_booking.attrs['net'] = Decimal("123.45")
        raw_booking.attrs['yesno'] = False
        from bda.plone.orders.common import BookingData
        booking = BookingData(self.portal, booking=raw_booking)
        return booking

    def test_serialization(self):
        booking = self._create_booking()
        self.assertDictEqual(
            self._serializer(booking)(),
            {'net': Decimal('123.45'), 'uid': 'Unique-Id-001', 'yesno': False},
        )
