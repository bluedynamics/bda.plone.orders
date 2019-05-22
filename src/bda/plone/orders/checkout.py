# -*- coding: utf-8 -*-
from bda.plone.cart import cookie
from bda.plone.cart.cart import get_data_provider
from bda.plone.cart.cartitem import get_item_data_provider
from bda.plone.cart.cartitem import get_item_state
from bda.plone.cart.cartitem import get_item_stock
from bda.plone.cart.utils import get_catalog_brain
from bda.plone.cart.utils import get_object_by_uid
from bda.plone.checkout import CheckoutAdapter
from bda.plone.checkout import CheckoutError
from bda.plone.orders import events
from bda.plone.orders import interfaces as ifaces
from bda.plone.orders import message_factory as _
from bda.plone.orders.common import acquire_vendor_or_shop_root
from bda.plone.orders.datamanagers.order import calculate_order_state
from bda.plone.orders.datamanagers.order import create_ordernumber
from bda.plone.orders.common import get_bookings_soup
from bda.plone.orders.common import get_orders_soup
from bda.plone.payment import Payments
from bda.plone.cart.shipping import Shippings
from bda.plone.cart.interfaces import IShippingItem
from decimal import Decimal
from node.ext.zodb import OOBTNode
from node.utils import instance_property
from plone.uuid.interfaces import IUUID
from repoze.catalog.query import Eq
from souper.soup import Record
from zope.component import queryAdapter
from zope.event import notify

import datetime
import logging
import plone.api
import uuid


logger = logging.getLogger(__name__)


class OrderCheckoutAdapter(CheckoutAdapter):
    @instance_property
    def order(self):
        return Record()

    @property
    def vessel(self):
        return self.order.attrs

    @property
    def items(self):
        # XXX here the ICartItemDataProvider implementation must be used
        return cookie.extractitems(cookie.read(self.request))

    def ordernumber_exists(self, soup, ordernumber):
        return bool(soup.query(Eq("ordernumber", ordernumber), with_size=True).next())

    def save(self, providers, widget, data):
        super(OrderCheckoutAdapter, self).save(providers, widget, data)
        order = self.order
        # order UUID
        uid = order.attrs["uid"] = uuid.uuid4()
        # order creator
        creator = None
        member = plone.api.user.get_current()
        if member:
            creator = member.getId()
        order.attrs["creator"] = creator
        # order creation date
        created = datetime.datetime.now()
        order.attrs["created"] = created
        cart_data = get_data_provider(self.context, self.request)
        # payment related information
        if cart_data.total > Decimal(0):
            payment_param = "checkout.payment_selection.payment"
            pid = data.fetch(payment_param).extracted
            payment = Payments(self.context).get(pid)
            order.attrs["payment_method"] = pid
            if payment:
                order.attrs["payment_label"] = payment.label
            else:
                order.attrs["payment_label"] = _("unknown", default=u"Unknown")
        # no payment
        else:
            order.attrs["payment_method"] = "no_payment"
            order.attrs["payment_label"] = _("no_payment", default=u"No Payment")
        # shipping related information
        if cart_data.include_shipping_costs:
            shipping_param = "checkout.shipping_selection.shipping"
            sid = data.fetch(shipping_param).extracted
            shipping = Shippings(self.context).get(sid)
            order.attrs["shipping_method"] = sid
            order.attrs["shipping_label"] = shipping.label
            order.attrs["shipping_description"] = shipping.description
            try:
                order.attrs["shipping_net"] = shipping.net(self.items)
                order.attrs["shipping_vat"] = shipping.vat(self.items)
                order.attrs["shipping"] = (
                    order.attrs["shipping_net"] + order.attrs["shipping_vat"]
                )
            # B/C for bda.plone.shipping < 0.4
            except NotImplementedError:
                order.attrs["shipping_net"] = shipping.calculate(self.items)
                order.attrs["shipping_vat"] = Decimal(0)
                order.attrs["shipping"] = order.attrs["shipping_net"]
        # no shipping
        else:
            order.attrs["shipping_method"] = "no_shipping"
            order.attrs["shipping_label"] = _("no_shipping", default=u"No Shipping")
            order.attrs["shipping_description"] = ""
            order.attrs["shipping_net"] = Decimal(0)
            order.attrs["shipping_vat"] = Decimal(0)
            order.attrs["shipping"] = Decimal(0)
        # create order bookings
        bookings = self.create_bookings(order)
        # set order state, needed for sorting in orders table
        order.attrs["state"] = calculate_order_state(bookings)
        # set order salaried, needed for sorting in orders table
        order.attrs["salaried"] = ifaces.SALARIED_NO
        # lookup booking uids, buyable uids and vendor uids
        booking_uids = list()
        buyable_uids = list()
        vendor_uids = set()
        for booking in bookings:
            booking_uids.append(booking.attrs["uid"])
            buyable_uids.append(booking.attrs["buyable_uid"])
            vendor_uids.add(booking.attrs["vendor_uid"])
        order.attrs["booking_uids"] = booking_uids
        order.attrs["buyable_uids"] = buyable_uids
        order.attrs["vendor_uids"] = list(vendor_uids)
        # cart discount related information
        # XXX: in order to be able to reliably modify orders, cart discount
        #      rules for this order must be stored instead of the actual
        #      calculated discount.
        cart_discount = cart_data.discount(self.items)
        order.attrs["cart_discount_net"] = cart_discount["net"]
        order.attrs["cart_discount_vat"] = cart_discount["vat"]
        # create ordernumber
        orders_soup = get_orders_soup(self.context)
        ordernumber = create_ordernumber()
        while self.ordernumber_exists(orders_soup, ordernumber):
            ordernumber = create_ordernumber()
        order.attrs["ordernumber"] = ordernumber
        # add order
        orders_soup.add(order)
        # add bookings
        bookings_soup = get_bookings_soup(self.context)
        # list containing items where stock threshold has been reached
        stock_threshold_reached_items = list()
        for booking in bookings:
            bookings_soup.add(booking)
            buyable = get_object_by_uid(self.context, booking.attrs["buyable_uid"])
            item_stock = get_item_stock(buyable)
            # no stock applied
            if item_stock is None:
                stock_warning_threshold = None
            else:
                stock_warning_threshold = item_stock.stock_warning_threshold
            if stock_warning_threshold:
                remaining = booking.attrs["remaining_stock_available"]
                # stock threshold has been reached
                if remaining <= stock_warning_threshold:
                    stock_threshold_reached_items.append(booking.attrs)
        if stock_threshold_reached_items:
            event = events.StockThresholdReached(
                self.context,
                self.request,
                order.attrs["uid"],
                stock_threshold_reached_items,
            )
            notify(event)
        # return uid of added order
        return uid

    def create_bookings(self, order):
        ret = list()
        cart_data = get_data_provider(self.context)
        for uid, count, comment in self.items:
            booking = self.create_booking(order, cart_data, uid, count, comment)
            if booking:
                ret.append(booking)
        return ret

    def create_booking(self, order, cart_data, uid, count, comment):
        brain = get_catalog_brain(self.context, uid)
        # brain could be None if uid for item in cookie which no longer exists.
        if not brain:
            msg = u"Item was removed from shop, uid={0}".format(uid)
            logger.warning(msg)
            raise CheckoutError(msg)
        buyable = brain.getObject()
        item_state = get_item_state(buyable, self.request)
        if not item_state.validate_count(count):
            msg = u"Item no longer available {0}".format(buyable.id)
            logger.warning(msg)
            raise CheckoutError(msg)
        item_stock = get_item_stock(buyable)
        # stock not applied, state new
        if item_stock is None:
            available = None
            state = ifaces.STATE_NEW
        # calculate state from stock
        else:
            if item_stock.available is not None:
                item_stock.available -= float(count)
            available = item_stock.available
            state = (
                ifaces.STATE_NEW
                if available is None or available >= 0.0
                else ifaces.STATE_RESERVED
            )
        item_data = get_item_data_provider(buyable)
        vendor = acquire_vendor_or_shop_root(buyable)
        booking = OOBTNode()
        booking.attrs["email"] = order.attrs["personal_data.email"]
        booking.attrs["uid"] = uuid.uuid4()
        booking.attrs["buyable_uid"] = uid
        booking.attrs["buyable_count"] = count
        booking.attrs["buyable_comment"] = comment
        booking.attrs["order_uid"] = order.attrs["uid"]
        booking.attrs["vendor_uid"] = uuid.UUID(IUUID(vendor))
        booking.attrs["creator"] = order.attrs["creator"]
        booking.attrs["created"] = order.attrs["created"]
        booking.attrs["exported"] = False
        booking.attrs["title"] = brain and brain.Title or "unknown"
        booking.attrs["net"] = item_data.net
        booking.attrs["vat"] = item_data.vat
        # XXX: in order to be able to reliably modify bookings, item discount
        #      rules for this booking must be stored instead of the actual
        #      calculated discount.
        booking.attrs["discount_net"] = item_data.discount_net(count)
        booking.attrs["currency"] = cart_data.currency
        booking.attrs["quantity_unit"] = item_data.quantity_unit
        booking.attrs["remaining_stock_available"] = available
        booking.attrs["state"] = state
        booking.attrs["salaried"] = ifaces.SALARIED_NO
        booking.attrs["tid"] = "none"
        shipping_info = queryAdapter(buyable, IShippingItem)
        booking.attrs["shippable"] = shipping_info and shipping_info.shippable
        trading_info = queryAdapter(buyable, ifaces.ITrading)
        booking.attrs["item_number"] = (
            trading_info.item_number if trading_info else None
        )
        booking.attrs["gtin"] = trading_info.gtin if trading_info else None
        return booking
