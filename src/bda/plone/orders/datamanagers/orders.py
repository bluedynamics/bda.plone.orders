# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from bda.plone.orders.common import acquire_vendor_or_shop_root
from bda.plone.orders.common import get_bookings_soup
from bda.plone.orders.common import get_orders_soup
from bda.plone.orders.common import get_vendor_uids_for
from bda.plone.orders.datamanagers.order import OrderData
from bda.plone.orders.interfaces.markers import IBuyable
from plone import api
from Products.CMFPlone.interfaces import IPloneSiteRoot
from repoze.catalog import query as rq

import uuid


class OrdersManager(object):
    """Manage orders in a given context
    """

    def __init__(self, context, vendor_uid=None):
        self.context = context
        self.vendor_uid = uuid.UUID(vendor_uid) if vendor_uid else None
        self.shop = acquire_vendor_or_shop_root(context)
        self.orders_soup = get_orders_soup(context)
        self.bookings_soup = get_bookings_soup(context)

    def orders_base_query(self):
        """Creates a base query object for the actual context.

        Idea is to use it and extend it by further filters.
        Takes current context and its vendors into account.
        If a vendor_uid is given, this vendor is filtered only.

        raises:
            Unauthorized the given vendor_uid is not part of the
            current context.

        returns:
            repoze catalog query
        """
        vendor_uids = get_vendor_uids_for()
        if self.vendor_uid is None:
            query = rq.Any("vendor_uids", vendor_uids)
        else:
            if self.vendor_uid not in vendor_uids:
                raise Unauthorized
            query = rq.Any("vendor_uids", [self.vendor_uid])
        if not IPloneSiteRoot.providedBy(self.context):
            buyable_uids = self._get_buyable_uids_in_context()
            query = rq.Any("buyable_uids", buyable_uids)
        return query

    def orders(self, query=None, sort_index=None, reverse=None):
        """iterator with length and records of orders

        query (repoze catalog query):
            query to filter on

        If a query is given, the vendor_uid is ignored.
        if neither query nor vendor_uid are given, all orders valid
        for the actual context and its vendors for the are returned.

        returns:
            iterator with first result length, then all following order records.
        """
        if query is not None:
            query = query & self.orders_base_query()
        else:
            query = self.orders_base_query()
        res = self.orders_soup.lazy(
            query, with_size=True, sort_index=sort_index, reverse=reverse
        )
        length = next(res)
        return length, res

    def orders_data(self, query=None, sort_index=None, reverse=None):
        """iterator with length and orderdata

        query (repoze catalog query):
            query to filter on

        If a query is given, the vendor_uid is ignored.
        if neither query nor vendor_uid are given, all orders valid
        for the actual context and its vendors for the are returned.

        returns:
            iterator with first result length, then all following OrderData
        """
        length, lazy_records = self.orders(query=query, sort_index=None, reverse=None)

        def orderdata_generator():
            for lazy_record in lazy_records:
                yield OrderData(self.context, order=lazy_record())

        return length, orderdata_generator()

    def _get_buyable_uids_in_context(self):
        for brain in api.content.find(
            context=self.context, object_provides=IBuyable.__identifier__
        ):
            yield brain.UID

    def remove(self, filter_query):
        """Remove all orders matching the query.

        Don't drink and use this.
        """
        query = self.orders_base_query()
        length, orderdata_iterator = self.orders_data(query=query)
        if length == 0:
            return False
        for orderdata in orderdata_iterator:
            # remove order and its bookings
            orderdata.remove()
        return True
