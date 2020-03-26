# -*- coding: utf-8 -*-
from bda.plone.orders.datamanagers.base import BaseState
from bda.plone.orders.datamanagers.base import calculate_order_state
from bda.plone.orders.datamanagers.order import OrderData
from bda.plone.orders.interfaces.orders import IBookingData
from repoze.catalog.query import Any
from repoze.catalog.query import Eq
from zope.interface import implementer

import uuid


def booking_update_comment(context, booking_uid, comment):
    booking_data = BookingData(context, uid=booking_uid)
    if booking_data.booking is None:
        raise ValueError("invalid value (booking)")
    booking = booking_data.booking
    booking.attrs["buyable_comment"] = comment
    booking_data.reindex()


@implementer(IBookingData)
class BookingData(BaseState):
    def __init__(self, context, uid=None, booking=None, vendor_uids=[]):
        """Create booking data object by criteria

        :param context: Context to work with
        :type object: Plone or Content instance
        :param uid: Booking uid. XOR with booking
        :type uid: string or uuid.UUID object
        :param booking: Booking record. XOR with uid
        :type booking: souper.soup.Record object
        :param vendor_uids: Vendor uids, used to filter order bookings.
        :type vendor_uids: List of vendor uids as string or uuid.UUID object.
        """
        if not (bool(uid) != bool(booking)):  # ^= xor
            raise ValueError("uid and booing are mutually exclusive")
        if uid and not isinstance(uid, uuid.UUID):
            uid = uuid.UUID(uid)
        vendor_uids = [uuid.UUID(str(vuid)) for vuid in vendor_uids]
        self.context = context
        self._uid = uid
        self._booking = booking

        self.vendor_uids = vendor_uids

    @property
    def uid(self):
        if self._uid:
            return self._uid
        return self.booking.attrs["uid"]

    def reindex(self):
        return

    @property
    def booking(self):
        if self._booking:
            return self._booking
        soup = self.bookings_soup
        query = Eq("uid", self.uid)
        if self.vendor_uids:
            query = query & Any("vendor_uid", self.vendor_uids)
        result = soup.query(query, with_size=True)
        length = next(result)
        if length != 1:  # first result is length
            return None
        self._booking = next(result)
        return self._booking

    @property
    def order(self):
        # XXX: rename to order_data for less confusion
        return OrderData(
            self.context,
            uid=self.booking.attrs["order_uid"],
            vendor_uids=self.vendor_uids,
        )

    @property
    def state(self):
        return self.booking.attrs["state"]

    @state.setter
    def state(self, value):
        # XXX: currently we need to delete attributes before setting to a new
        #      value in order to persist change. fix in appropriate place.
        booking = self.booking
        self.update_item_stock(booking, booking.attrs["state"], value)
        del booking.attrs["state"]
        booking.attrs["state"] = value
        order = self.order
        del order.order.attrs["state"]
        order.order.attrs["state"] = calculate_order_state(order.bookings)
        self.reindex_bookings([booking])
        self.reindex_order(order.order)

    @property
    def salaried(self):
        return self.booking.attrs["salaried"]

    @salaried.setter
    def salaried(self, value):
        # XXX: currently we need to delete attributes before setting to a new
        #      value in order to persist change. fix in appropriate place.
        booking = self.booking
        del booking.attrs["salaried"]
        booking.attrs["salaried"] = value
        order = self.order
        del order.order.attrs["salaried"]
        order.order.attrs["salaried"] = calculate_order_salaried(order.bookings)  # noqa
        self.reindex_bookings([booking])
        self.reindex_order(order.order)
