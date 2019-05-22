# -*- coding: utf-8 -*-
from bda.plone.orders.common import get_bookings_soup
from bda.plone.orders.interfaces.markers import IBuyable
from decimal import Decimal
from plone.uuid.interfaces import IUUID
from repoze.catalog.query import Eq


class BuyableData(object):
    def __init__(self, context):
        if not IBuyable.providedBy(context):
            raise ValueError("Given context is not IBuyable")
        self.context = context

    def item_ordered(self, state=[]):
        """Return total count buyable item was ordered.
        """
        context = self.context
        bookings_soup = get_bookings_soup(context)
        order_bookings = dict()
        for booking in bookings_soup.query(Eq("buyable_uid", IUUID(context))):
            bookings = order_bookings.setdefault(booking.attrs["order_uid"], list())
            bookings.append(booking)
        count = Decimal("0")
        for order_uid, bookings in order_bookings.items():
            for booking in bookings:
                if state and booking.attrs["state"] not in state:
                    continue
                count += booking.attrs["buyable_count"]
        return count
