# -*- coding: utf-8 -*-
from bda.plone.cart.restapi.converter import json_compatible_dict
from bda.plone.orders.datamanagers.booking import BookingData
from bda.plone.orders.interfaces.orders import IBookingData
from bda.plone.orders.interfaces.orders import IOrderData
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.publisher.interfaces import IRequest


@implementer(ISerializeToJson)
@adapter(IBookingData, IRequest)
class SerializeBookingToJson(object):
    def __init__(self, booking_dm, request):
        self.booking_dm = booking_dm
        self.request = request

    def __call__(self):
        data = dict(self.booking_dm.booking.attrs)
        try:
            obj = api.content.get(
                UID=self.booking_dm.booking.attrs['buyable_uid'],
            )
            data['path'] = "/".join(obj.getPhysicalPath())
        except ValueError:
            data['path'] = None
        return json_compatible_dict(data)


@implementer(ISerializeToJson)
@adapter(IOrderData, IRequest)
class SerializeOrderToJson(object):
    def __init__(self, order_dm, request):
        self.order_dm = order_dm
        self.request = request

    def __call__(self):
        result = {
            "order": json_compatible_dict(dict(self.order_dm.order.attrs)),
            "bookings": [],
        }
        for booking_record in self.order_dm.bookings:
            serializer = getMultiAdapter(
                (
                    BookingData(
                        self.order_dm.context, booking=booking_record, vendor_uids=[]
                    ),
                    self.request,
                ),
                ISerializeToJson,
            )
            result["bookings"].append(serializer())
        return result
