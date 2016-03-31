# -*- coding: utf-8 -*-
from bda.plone.orders.interfaces import IBookingCancelledEvent
from bda.plone.orders.interfaces import IStockThresholdReached
from zope.interface import implementer


@implementer(IBookingCancelledEvent)
class BookingCancelledEvent(object):

    def __init__(self, context, request, order_uid, booking_attrs):
        self.context = context
        self.request = request
        self.order_uid = order_uid
        self.booking_attrs = booking_attrs

@implementer(IStockThresholdReached)
class StockThresholdReached(object):
    
    def __init__(self, context, request, order_uid, items_stock_threshold_reached):
        self.context = context
        self.request = request
        self.order_uid = order_uid
        self.items_stock_threshold_reached = items_stock_threshold_reached
