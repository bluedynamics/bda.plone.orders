# -*- coding: utf-8 -*-
from bda.plone.cart.cartitem import get_item_stock
from bda.plone.cart.utils import get_object_by_uid
from bda.plone.orders.common import get_bookings_soup
from bda.plone.orders.common import get_orders_soup
from bda.plone.orders.interfaces import IOrderState
from bda.plone.orders.interfaces import workflow
from node.utils import instance_property
from zope.interface import implementer


@implementer(IOrderState)
class BaseState(object):
    context = None

    @instance_property
    def orders_soup(self):
        return get_orders_soup(self.context)

    @instance_property
    def bookings_soup(self):
        return get_bookings_soup(self.context)

    def reindex_order(self, order):
        self.orders_soup.reindex(records=[order])

    def reindex_bookings(self, bookings):
        self.bookings_soup.reindex(records=bookings)

    @property
    def state(self):
        raise NotImplementedError("Abstract OrderState does not implement state")

    @state.setter
    def state(self, value):
        raise NotImplementedError("Abstract OrderState does not implement state.setter")

    @property
    def salaried(self):
        raise NotImplementedError("Abstract OrderState does not implement salaried")

    @salaried.setter
    def salaried(self, value):
        raise NotImplementedError(
            "Abstract OrderState does not implement salaried.setter"
        )

    def update_item_stock(self, booking, old_state, new_state):
        """Change stock according to transition. See table in transitions.py
        """
        if old_state == new_state:
            return
        # XXX: fix stock item available??
        if old_state == workflow.STATE_NEW:
            if new_state == workflow.STATE_CANCELLED:
                self.increase_stock(booking)
        elif old_state == workflow.STATE_RESERVED:
            if new_state in (workflow.STATE_PROCESSING, workflow.STATE_FINISHED):
                self.decrease_stock(booking)
        elif old_state == workflow.STATE_PROCESSING:
            if new_state == workflow.STATE_CANCELLED:
                self.increase_stock(booking)
        elif old_state == workflow.STATE_FINISHED:
            if new_state == workflow.STATE_NEW:
                # do nothing
                pass
        elif old_state == workflow.STATE_CANCELLED:
            if new_state == workflow.STATE_NEW:
                self.decrease_stock(booking)

    def increase_stock(self, booking):
        obj = get_object_by_uid(self.context, booking.attrs["buyable_uid"])
        # object no longer exists
        if not obj:
            return
        stock = get_item_stock(obj)
        # if stock.available is None, no stock information used
        if stock.available is not None:
            stock.available += float(booking.attrs["buyable_count"])

    def decrease_stock(self, booking):
        obj = get_object_by_uid(self.context, booking.attrs["buyable_uid"])
        # object no longer exists
        if not obj:
            return
        stock = get_item_stock(obj)
        # if stock.available is None, no stock information used
        if stock.available is not None:
            # TODO: ATTENTION: here might get removed more than available..?
            stock.available -= float(booking.attrs["buyable_count"])


def _calculate_order_attr_from_bookings(bookings, attr, mixed_value):
    ret = None
    for booking in bookings:
        val = booking.attrs[attr]
        if ret and ret != val:
            ret = mixed_value
            break
        else:
            ret = val
    return ret


def calculate_order_state(bookings):
    return _calculate_order_attr_from_bookings(bookings, "state", workflow.STATE_MIXED)


def calculate_order_salaried(bookings):
    return _calculate_order_attr_from_bookings(
        list(filter(is_billable_booking, bookings)), "salaried", workflow.SALARIED_MIXED
    )
