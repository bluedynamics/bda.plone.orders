# -*- coding: utf-8 -*-
from zope.interface import Attribute
from zope.interface import Interface


class IOrderSuccessfulEvent(Interface):
    """Checkout related event.
    """

    context = Attribute(u"Context in which this event was triggered.")
    request = Attribute(u"Current request.")
    order_uid = Attribute(u"UUID of Order")
    booking_attrs = Attribute(u"Dict of attributes of the cancelled booking.")


class IBookingCancelledEvent(Interface):
    """Checkout related event.
    """

    context = Attribute(u"Context in which this event was triggered.")
    request = Attribute(u"Current request.")
    order_uid = Attribute(u"UUID of Order")
    booking_attrs = Attribute(u"Dict of attributes of the cancelled booking.")


class IBookingReservedToOrderedEvent(Interface):
    """Checkout related event.
    """

    context = Attribute(u"Context in which this event was triggered.")
    request = Attribute(u"Current request.")
    order_uid = Attribute(u"UUID of Order")
    booking_attrs = Attribute(u"Dict of attributes of the cancelled booking.")


class IStockThresholdReached(Interface):
    """Checkout related event.
    """

    context = Attribute(u"Context in which this event was triggered.")
    request = Attribute(u"Current request.")
    order_uid = Attribute(u"UUID of Order")
    stock_threshold_reached_items = Attribute(
        u"List of items that are " u"getting out of stock."
    )
