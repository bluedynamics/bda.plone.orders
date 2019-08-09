# -*- coding: utf-8 -*-
from bda.plone.orders.common import get_order
from bda.plone.orders.common import is_billable_booking
from bda.plone.orders.datamanagers.base import BaseState
from bda.plone.orders.datamanagers.base import calculate_order_salaried
from bda.plone.orders.datamanagers.base import calculate_order_state
from bda.plone.orders.interfaces.orders import IOrderData
from decimal import Decimal
from repoze.catalog.query import Any
from repoze.catalog.query import Eq
from six.moves import filter
from zope.interface import implementer

import time
import uuid


def create_ordernumber():
    onum = hash(time.time())
    if onum < 0:
        return "0{0:d}".format(abs(onum))
    return "1{0:d}".format(onum)


@implementer(IOrderData)
class OrderData(BaseState):
    """Object for extracting order information.
    """

    def __init__(self, context, uid=None, order=None, vendor_uids=[]):
        """Create order data object by criteria

        :param context: Context to work with
        :type object: Plone or Content instance
        :param uid: Order uid. XOR with order
        :type uid: string or uuid.UUID object
        :param order: Order record. XOR with uid
        :type order: souper.soup.Record object
        :param vendor_uids: Vendor uids, used to filter order bookings.
        :type vendor_uids: List of vendor uids as string or uuid.UUID object.
        """
        if not (bool(uid) != bool(order)):  # ^= xor
            raise ValueError("Parameters 'uid' and 'order' are mutually exclusive.")
        if uid and not isinstance(uid, uuid.UUID):
            uid = uuid.UUID(uid)
        vendor_uids = [uuid.UUID(str(vuid)) for vuid in vendor_uids]
        self.context = context
        self._uid = uid
        self._order = order
        self.vendor_uids = vendor_uids

    @property
    def uid(self):
        if self._uid:
            return self._uid
        return self.order.attrs["uid"]

    @property
    def order(self):
        if self._order:
            return self._order
        return get_order(self.context, self.uid)

    @property
    def bookings(self):
        soup = self.bookings_soup
        query = Eq("order_uid", self.uid)
        if self.vendor_uids:
            query = query & Any("vendor_uid", self.vendor_uids)
        return soup.query(query)

    @property
    def currency(self):
        ret = None
        for booking in self.bookings:
            val = booking.attrs["currency"]
            if ret and ret != val:
                msg = (
                    u"Order contains bookings with inconsistent "
                    u"currencies {0} != {1}".format(ret, val)
                )
                raise ValueError(msg)
            ret = val
        return ret

    @property
    def state(self):
        return calculate_order_state(self.bookings)

    @state.setter
    def state(self, value):
        # XXX: currently we need to delete attributes before setting to a new
        #      value in order to persist change. fix in appropriate place.
        bookings = self.bookings
        for booking in bookings:
            self.update_item_stock(booking, booking.attrs["state"], value)
            del booking.attrs["state"]
            booking.attrs["state"] = value
        order = self.order
        del order.attrs["state"]
        order.attrs["state"] = value
        self.reindex_bookings(bookings)
        self.reindex_order(order)

    @property
    def salaried(self):
        return calculate_order_salaried(self.bookings)

    @salaried.setter
    def salaried(self, value):
        # XXX: currently we need to delete attributes before setting to a new
        #      value in order to persist change. fix in appropriate place.
        bookings = self.bookings
        for booking in bookings:
            del booking.attrs["salaried"]
            booking.attrs["salaried"] = value
        order = self.order
        del order.attrs["salaried"]
        order.attrs["salaried"] = value
        self.reindex_bookings(bookings)
        self.reindex_order(order)

    @property
    def tid(self):
        ret = set()
        for booking in self.bookings:
            tid = booking.attrs.get("tid", None)
            if tid:
                ret.add(tid)
        return ret

    @tid.setter
    def tid(self, value):
        for booking in self.bookings:
            booking.attrs["tid"] = value

    @property
    def net(self):
        ret = Decimal(0)
        for booking in filter(is_billable_booking, self.bookings):
            count = Decimal(booking.attrs["buyable_count"])
            net = Decimal(booking.attrs.get("net", 0))
            discount_net = Decimal(booking.attrs["discount_net"])
            ret += (net - discount_net) * count
        return ret

    @property
    def vat(self):
        ret = Decimal(0)
        for booking in filter(is_billable_booking, self.bookings):
            count = Decimal(booking.attrs["buyable_count"])
            net = Decimal(booking.attrs.get("net", 0))
            discount_net = Decimal(booking.attrs["discount_net"])
            item_net = net - discount_net
            ret += (item_net * Decimal(booking.attrs.get("vat", 0)) / 100) * count
        return ret

    @property
    def discount_net(self):
        return Decimal(self.order.attrs["cart_discount_net"])

    @property
    def discount_vat(self):
        return Decimal(self.order.attrs["cart_discount_vat"])

    @property
    def shipping_net(self):
        return Decimal(self.order.attrs["shipping_net"])

    @property
    def shipping_vat(self):
        return Decimal(self.order.attrs["shipping_vat"])

    @property
    def shipping(self):
        return Decimal(self.order.attrs["shipping"])

    @property
    def total(self):
        # XXX: use decimal
        total = self.net - self.discount_net + self.vat - self.discount_vat
        return total + self.shipping

    def remove(self):
        """removes this order from the database.
        """
        raise NotImplemented
