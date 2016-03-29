# -*- coding: utf-8 -*-
from bda.plone.orders.interfaces import IBookingCancelledEvent
from bda.plone.orders.interfaces import IItemOutOfStockEvent
from zope.interface import implementer


@implementer(IBookingCancelledEvent)
class BookingCancelledEvent(object):

    def __init__(self, context, request, order_uid, booking_attrs):
        self.context = context
        self.request = request
        self.order_uid = order_uid
        self.booking_attrs = booking_attrs

@implementer(IItemOutOfStockEvent)
class ItemOutOfStockEvent(object):
    
    def __init__(self, context, request, order_uid, items_out_of_stock):
        self.context = context
        self.request = request
        self.order_uid = order_uid
        self.items_out_of_stock = items_out_of_stock
