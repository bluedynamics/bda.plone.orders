# -*- coding: utf-8 -*-
from bda.plone.cart.restapi.converter import json_compatible_dict
from bda.plone.orders.datamanager.booking import BookingData
from bda.plone.orders.interfaces.orders import IBookingData
from bda.plone.orders.interfaces.orders import IOrderData
from plone.restapi.interfaces import ISerializeToJson
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.publisher.interfaces import IRequest


@implementer(ISerializeToJson)
@adapter(IBookingData, IRequest)
class SerializeBookingToJson(object):
    def __init__(self, booking, request):
        self.booking = booking
        self.request = request

    def __call__(self):
        return json_compatible_dict(dict(self.booking.booking.attrs))


@implementer(ISerializeToJson)
@adapter(IOrderData, IRequest)
class SerializeOrderToJson(object):
    def __init__(self, order, request):
        self.order = order
        self.request = request

    def __call__(self):
        result = {
            "order": json_compatible_dict(dict(self.order.order.attrs)),
            "bookings": [],
        }
        for booking_record in self.order.bookings:
            serializer = getMultiAdapter(
                (
                    BookingData(
                        self.order.context, booking=booking_record, vendor_uids=[]
                    ),
                    self.request,
                ),
                ISerializeToJson,
            )
            result["bookings"].append(serializer())
        return result
