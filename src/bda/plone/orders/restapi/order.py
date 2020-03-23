# -*- coding: utf-8 -*-
from bda.plone.cart.restapi.service import Service
from bda.plone.cart.restapi.service import TraversingService
from bda.plone.orders.common import get_vendor_uids_for
from bda.plone.orders.datamanagers.order import OrderData
from bda.plone.orders.datamanagers.orders import OrdersManager
from plone.restapi.interfaces import ISerializeToJson
from repoze.catalog.query import Any
from repoze.catalog.query import Eq
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

class QueryOrdersService(Service):
    """List Orders by given Query for current users vendor

    supported queries (for now, to be extended):
        - state - list with one or more out of:
            cancelled
            finished
            mixed
            new
            processing
            reserved
    """

    def reply(self):
        states =  self.request.form.get("state", [])
        if not isinstance(states, list):
            states = [states]
        query = None  # build a repoze catalog query
        if states:
            query = Any("state", states)
        sort_index = self.request.form.get("sort_on", "created")
        reverse = self.request.form.get("sort_order", "") == "reverse"
        manager = OrdersManager(self.context)
        length, orders = manager.orders_data(query, sort_index, reverse)
        result = {
            "length": length,
            "orders": [],
        }
        for order in orders:
            serializer = getMultiAdapter((order, self.request), ISerializeToJson)
            result.append(serializer())
        return result
