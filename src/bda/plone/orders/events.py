# -*- coding: utf-8 -*-
from bda.plone.orders.interfaces import IBookingCancelledEvent
from bda.plone.orders.interfaces import IBookingReservedToOrderedEvent
from bda.plone.orders.interfaces import IOrderSuccessfulEvent
from bda.plone.orders.interfaces import IStockThresholdReached
from zope.interface import implementer


@implementer(IOrderSuccessfulEvent)
class OrderSuccessfulEvent(object):
    def __init__(self, context, request, order_uid, booking_attrs=None):
        self.context = context
        self.request = request
        self.order_uid = order_uid
        self.booking_attrs = booking_attrs


@implementer(IBookingCancelledEvent)
class BookingCancelledEvent(object):
    def __init__(self, context, request, order_uid, booking_attrs):
        self.context = context
        self.request = request
        self.order_uid = order_uid
        self.booking_attrs = booking_attrs


@implementer(IBookingReservedToOrderedEvent)
class BookingReservedToOrderedEvent(object):
    def __init__(self, context, request, order_uid, booking_attrs):
        self.context = context
        self.request = request
        self.order_uid = order_uid
        self.booking_attrs = booking_attrs


@implementer(IStockThresholdReached)
class StockThresholdReached(object):
    def __init__(self, context, request, order_uid, stock_threshold_reached_items):
        self.context = context
        self.request = request
        self.order_uid = order_uid
        self.stock_threshold_reached_items = stock_threshold_reached_items
