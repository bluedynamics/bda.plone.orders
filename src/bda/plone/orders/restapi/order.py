# -*- coding: utf-8 -*-
from bda.plone.orders.common import OrderData
from bda.plone.cart.restapi.service import TraversingService
from plone.restapi.interfaces import ISerializeToJson
from zope.component import getMultiAdapter


class OrderService(TraversingService):
    """Single Order with bookings"""

    def reply(self):
        if len(self.params) != 1:
            raise Exception(
                "Must supply exactly one parameter (identifier of"
                "the order) to be retrieved."
            )
        serializer = getMultiAdapter(
            (OrderData(self.context, uid=self.params[0]), self.request),
            ISerializeToJson,
        )
        return serializer()
