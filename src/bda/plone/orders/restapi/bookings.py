# -*- coding: utf-8 -*-
from bda.plone.cart.restapi.service import Service
from bda.plone.orders.common import get_vendor_uids_for
from bda.plone.orders.datamanagers.order import OrderData
from bda.plone.orders.datamanagers.orders import OrdersManager
from plone.restapi.interfaces import ISerializeToJson
from repoze.catalog.query import Any
from repoze.catalog.query import Eq
from zope.component import getMultiAdapter

class BookingsStateChangeService(Service):
    """Change State of given Bookings"""

    def reply(self):

        return {"result": "ok"}