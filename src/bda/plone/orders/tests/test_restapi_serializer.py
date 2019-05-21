# -*- coding: utf-8 -*-
from bda.plone.orders.tests import Orders_INTEGRATION_TESTING
from bda.plone.orders.tests import set_browserlayer
from decimal import Decimal
from plone.restapi.interfaces import ISerializeToJson
from zope.component import getMultiAdapter

import unittest


class TestSerializers(unittest.TestCase):
    layer = Orders_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        set_browserlayer(self.request)
        self.count = 1

    def _serializer(self, obj):
        serializer = getMultiAdapter((obj, self.request), ISerializeToJson)
        return serializer

    def _create_raw_record(self):
        from node.ext.zodb import OOBTNode

        record = OOBTNode()
        record.attrs["uid"] = "Unique-Id-{0:04d}".format(self.count)
        self.count += 1
        record.attrs["net"] = Decimal("123.45")
        record.attrs["yesno"] = False
        return record

    def _create_booking(self, order_uid=None):
        record = self._create_raw_record()
        from bda.plone.orders.common import get_bookings_soup

        bookings_soup = get_bookings_soup(self.portal)
        if order_uid:
            record.attrs["order_uid"] = order_uid
        bookings_soup.add(record)
        from bda.plone.orders.common import BookingData

        booking = BookingData(self.portal, booking=record)
        return booking

    def _create_order(self, bookings=1):
        record = self._create_raw_record()
        record.attrs["order_uids"] = []
        for count in range(0, bookings):
            booking = self._create_booking(order_uid=record.attrs["uid"])
            record.attrs["order_uids"].append(booking.uid)
        from bda.plone.orders.common import get_orders_soup

        orders_soup = get_orders_soup(self.portal)
        orders_soup.add(record)
        from bda.plone.orders.common import OrderData

        order = OrderData(self.portal, order=record)
        return order

    def test_booking_serialization(self):
        booking = self._create_booking()
        self.assertDictEqual(
            {'net': 123.45, 'uid': u'Unique-Id-0001', 'yesno': False},
            self._serializer(booking)(),
        )

    def test_order_serialization(self):
        order = self._create_order()
        self.assertDictEqual(
            {
                "bookings": [
                    {
                        "net": 123.45,
                        "order_uid": "Unique-Id-0001",
                        "uid": "Unique-Id-0002",
                        "yesno": False,
                    }
                ],
                "order": {
                    "net": 123.45,
                    "order_uids": ["Unique-Id-0002"],
                    "uid": "Unique-Id-0001",
                    "yesno": False,
                },
            },
            self._serializer(order)(),
        )
