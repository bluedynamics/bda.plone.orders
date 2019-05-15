# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from Acquisition import aq_parent
from bda.plone.cart import get_item_stock
from bda.plone.cart import get_object_by_uid
from bda.plone.orders import permissions
from bda.plone.orders import safe_encode
from bda.plone.orders.interfaces.markers import IBuyable
from bda.plone.orders.interfaces.markers import IVendor
from bda.plone.orders.interfaces.orders import IOrderState
from bda.plone.orders.interfaces.orders import IOrderData
from bda.plone.orders.interfaces.orders import IBookingData
from bda.plone.orders.interfaces import workflow
from bda.plone.payment.interfaces import IPaymentData
from decimal import Decimal
from node.utils import instance_property
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.interfaces import IPloneSiteRoot
from repoze.catalog.query import Any
from repoze.catalog.query import Eq
from six.moves import filter
from souper.soup import get_soup
from zope.deferredimport import deprecated
from zope.interface import implementer

import logging
import plone.api
import time
import uuid

deprecated(
    "Import from new location instead",
    BookingsCatalogFactory="bda.plone.orders.catalogfactories:BookingsCatalogFactory",
    OrdersCatalogFactory="bda.plone.orders.catalogfactories:OrdersCatalogFactory",
    OrderCheckoutAdapter="bda.plone.orders.checkout:OrderCheckoutAdapter",
)

logger = logging.getLogger(__name__)


DT_FORMAT = "%d.%m.%Y %H:%M"
DT_FORMAT_SHORT = "%d.%m.%Y"


def create_ordernumber():
    onum = hash(time.time())
    if onum < 0:
        return "0%s" % str(abs(onum))
    return "1%s" % str(onum)


def get_orders_soup(context):
    return get_soup("bda_plone_orders_orders", context)


def get_bookings_soup(context):
    return get_soup("bda_plone_orders_bookings", context)


def get_order(context, uid):
    if not isinstance(uid, uuid.UUID):
        uid = uuid.UUID(uid)
    soup = get_orders_soup(context)
    return [it for it in soup.query(Eq("uid", uid))][0]


def acquire_vendor_or_shop_root(context):
    """Returns the acquired vendor or the main shop by traversing up the
    content tree, starting from a context.

    :param context: The context to start searching for the nearest vendor.
    :type context: Content object
    :returns: The vendor, a shop item is belonging to.
    :rtype: Content object
    """
    if not context:
        message = u"No context given to acquire vendor or shop root from"
        raise ValueError(message)
    while not IVendor.providedBy(context) and not IPloneSiteRoot.providedBy(
        context
    ):
        context = aq_parent(aq_inner(context))
    return context


def get_all_vendors():
    """Get all available vendor areas.

    :returns: Vendor area enabled content objects.
    :rtype: List of content objects.
    """
    cat = plone.api.portal.get_tool("portal_catalog")
    query = {"object_provides": IVendor.__identifier__}
    vendors = [brain.getObject() for brain in cat(**query)]
    return vendors + [plone.api.portal.get()]


def get_vendor_by_uid(context, vendor_uid):
    """Return vendor object by uid or site root as fallback if requested vendor
    not exists.

    :param vendor_uid: Vendor uid.
    :type vendor_uid: string or uuid.UUID object
    :returns: Vendor Object
    :rtype: IVendor implementing content Object
    """
    if not isinstance(vendor_uid, uuid.UUID):
        vendor_uid = uuid.UUID(vendor_uid)
    vendor = get_object_by_uid(context, vendor_uid)
    if vendor is None:
        vendor = plone.api.portal.get()
    return vendor


def get_vendors_for(user=None):
    """Gel all vendor containers a given or authenticated user has vendor
    permissions for.

    :param user: Optional user object to check permissions on vendor areas. If
                 no user object is give, the current user is used.
    :type user: MemberData object
    :returns: Allowed vendor area enabled content objects.
    :rtype: List of content objects.
    """
    if user is None:
        user = plone.api.user.get_current()

    def permitted(obj):
        return plone.api.user.has_permission(permissions.ModifyOrders, obj=obj)

    return [vendor for vendor in get_all_vendors() if permitted(vendor)]


def get_vendor_uids_for(user=None):
    """Gel all vendor container uids a given or authenticated user has vendor
    permissions for.

    :param user: Optional user object to check permissions on vendor areas. If
                 no user object is give, the current user is used.
    :type user: MemberData object
    :returns: Allowed vendor area uids for given or authenticated member.
    :rtype: List of uuid.UUID objects.
    """
    return [uuid.UUID(IUUID(vendor)) for vendor in get_vendors_for(user=user)]


# TODO: used in vocabularies, remove if possible
def get_vendor_order_uids_for(context, user=None):
    """Get order uids all orders a given or current user has vendor
    permissions for.

    :param user: Optional user object to check permissions on vendor areas. If
                 no user object is give, the current user is used.
    :type user: MemberData object
    :returns: List of order UUID objects.
    :rtype: List of uuid.UUID
    """
    vendors = get_vendor_uids_for(user=user)
    soup = get_bookings_soup(context)
    res = soup.query(Any("vendor_uid", vendors))
    order_uids = {booking.attrs["order_uid"] for booking in res}
    return order_uids


# Patch this tuple with booking states which should be ignored at initial
# billing.
# WARNING: see notes in ``is_billable_booking`` docs.
BOOKING_BILLABLE_IGNORE_STATES = tuple()


def is_billable_booking(booking):
    """Return True, if booking is billable and should be included in order
    summary calculations.

    To be used in Pythons filter function:

        filter(is_billable_booking, bookings)

    WARNING:

    This function has been added for bda.plone.ticketshop to skip billing
    sold out tickets. When selling tickets, a backorder is handled that
    someone waits until a ticket order from another customer gets cancelled.

    But this behavior does not apply to most shop implementations where goods
    are sold. Here a backorder normally means a temporary unavailability of
    buyable items and has effect to delivery time, not billing.

    Since bda.plone.orders does not properly implement the full UI to handle
    partly billed bookings (carry back unbilled backorders, incomplete order
    and invoive views), this function is treated as hack, but is not removed
    due to the needs of ticketshop unless the related usecase is properly
    implemented.

    See https://github.com/bluedynamics/bda.plone.orders/issues/45
    """
    return booking.attrs["state"] not in BOOKING_BILLABLE_IGNORE_STATES


def _calculate_order_attr_from_bookings(bookings, attr, mixed_value):
    ret = None
    for booking in bookings:
        val = booking.attrs[attr]
        if ret and ret != val:
            ret = mixed_value
            break
        else:
            ret = val
    return ret


def calculate_order_state(bookings):
    return _calculate_order_attr_from_bookings(
        bookings, "state", workflow.STATE_MIXED
    )


def calculate_order_salaried(bookings):
    return _calculate_order_attr_from_bookings(
        list(filter(is_billable_booking, bookings)),
        "salaried",
        workflow.SALARIED_MIXED,
    )


@implementer(IOrderState)
class OrderState(object):
    context = None

    @instance_property
    def orders_soup(self):
        return get_orders_soup(self.context)

    @instance_property
    def bookings_soup(self):
        return get_bookings_soup(self.context)

    def reindex_order(self, order):
        self.orders_soup.reindex(records=[order])

    def reindex_bookings(self, bookings):
        self.bookings_soup.reindex(records=bookings)

    @property
    def state(self):
        raise NotImplementedError(
            "Abstract OrderState does not implement state"
        )

    @state.setter
    def state(self, value):
        raise NotImplementedError(
            "Abstract OrderState does not implement state.setter"
        )

    @property
    def salaried(self):
        raise NotImplementedError(
            "Abstract OrderState does not implement salaried"
        )

    @salaried.setter
    def salaried(self, value):
        raise NotImplementedError(
            "Abstract OrderState does not implement salaried.setter"
        )

    def update_item_stock(self, booking, old_state, new_state):
        """Change stock according to transition. See table in transitions.py
        """
        if old_state == new_state:
            return
        # XXX: fix stock item available??
        if old_state == workflow.STATE_NEW:
            if new_state == workflow.STATE_CANCELLED:
                self.increase_stock(booking)
            else:
                # do nothing
                pass
        elif old_state == workflow.STATE_RESERVED:
            if new_state in (
                workflow.STATE_PROCESSING,
                workflow.STATE_FINISHED,
            ):
                self.decrease_stock(booking)
            else:
                # do nothing
                pass
        elif old_state == workflow.STATE_PROCESSING:
            if new_state == workflow.STATE_CANCELLED:
                self.increase_stock(booking)
            else:
                # do nothing
                pass
        elif old_state == workflow.STATE_FINISHED:
            if new_state == workflow.STATE_NEW:
                # do nothing
                pass
        elif old_state == workflow.STATE_CANCELLED:
            if new_state == workflow.STATE_NEW:
                self.decrease_stock(booking)
            else:
                # do nothing
                pass

    def increase_stock(self, booking):
        obj = get_object_by_uid(self.context, booking.attrs["buyable_uid"])
        # object no longer exists
        if not obj:
            return
        stock = get_item_stock(obj)
        # if stock.available is None, no stock information used
        if stock.available is not None:
            stock.available += float(booking.attrs["buyable_count"])

    def decrease_stock(self, booking):
        obj = get_object_by_uid(self.context, booking.attrs["buyable_uid"])
        # object no longer exists
        if not obj:
            return
        stock = get_item_stock(obj)
        # if stock.available is None, no stock information used
        if stock.available is not None:
            # TODO: ATTENTION: here might get removed more than available..?
            stock.available -= float(booking.attrs["buyable_count"])


@implementer(IOrderData)
class OrderData(OrderState):
    """Object for extracting order information.
    """

    def __init__(self, context, uid=None, order=None, vendor_uids=[]):
        """Create order data object by criteria

        :param context: Context to work with
        :type object: Plone or Content instance
        :param uid: Order uid. XOR with order
        :type uid: string or uuid.UUID object
        :param order: Order record. XOR with uid
        :type order: souper.soup.Record object
        :param vendor_uids: Vendor uids, used to filter order bookings.
        :type vendor_uids: List of vendor uids as string or uuid.UUID object.
        """
        if not (bool(uid) != bool(order)):  # ^= xor
            raise ValueError(
                "Parameters 'uid' and 'order' are mutually exclusive."
            )
        if uid and not isinstance(uid, uuid.UUID):
            uid = uuid.UUID(uid)
        vendor_uids = [uuid.UUID(str(vuid)) for vuid in vendor_uids]
        self.context = context
        self._uid = uid
        self._order = order
        self.vendor_uids = vendor_uids

    @property
    def uid(self):
        if self._uid:
            return self._uid
        return self.order.attrs["uid"]

    @property
    def order(self):
        if self._order:
            return self._order
        return get_order(self.context, self.uid)

    @property
    def bookings(self):
        soup = self.bookings_soup
        query = Eq("order_uid", self.uid)
        if self.vendor_uids:
            query = query & Any("vendor_uid", self.vendor_uids)
        return soup.query(query)

    @property
    def currency(self):
        ret = None
        for booking in self.bookings:
            val = booking.attrs["currency"]
            if ret and ret != val:
                msg = (
                    u"Order contains bookings with inconsistent "
                    u"currencies {0} != {1}".format(ret, val)
                )
                raise ValueError(msg)
            ret = val
        return ret

    @property
    def state(self):
        return calculate_order_state(self.bookings)

    @state.setter
    def state(self, value):
        # XXX: currently we need to delete attributes before setting to a new
        #      value in order to persist change. fix in appropriate place.
        bookings = self.bookings
        for booking in bookings:
            self.update_item_stock(booking, booking.attrs["state"], value)
            del booking.attrs["state"]
            booking.attrs["state"] = value
        order = self.order
        del order.attrs["state"]
        order.attrs["state"] = value
        self.reindex_bookings(bookings)
        self.reindex_order(order)

    @property
    def salaried(self):
        return calculate_order_salaried(self.bookings)

    @salaried.setter
    def salaried(self, value):
        # XXX: currently we need to delete attributes before setting to a new
        #      value in order to persist change. fix in appropriate place.
        bookings = self.bookings
        for booking in bookings:
            del booking.attrs["salaried"]
            booking.attrs["salaried"] = value
        order = self.order
        del order.attrs["salaried"]
        order.attrs["salaried"] = value
        self.reindex_bookings(bookings)
        self.reindex_order(order)

    @property
    def tid(self):
        ret = set()
        for booking in self.bookings:
            tid = booking.attrs.get("tid", None)
            if tid:
                ret.add(tid)
        return ret

    @tid.setter
    def tid(self, value):
        for booking in self.bookings:
            booking.attrs["tid"] = value

    @property
    def net(self):
        ret = Decimal(0)
        for booking in filter(is_billable_booking, self.bookings):
            count = Decimal(booking.attrs["buyable_count"])
            net = Decimal(booking.attrs.get("net", 0))
            discount_net = Decimal(booking.attrs["discount_net"])
            ret += (net - discount_net) * count
        return ret

    @property
    def vat(self):
        ret = Decimal(0)
        for booking in filter(is_billable_booking, self.bookings):
            count = Decimal(booking.attrs["buyable_count"])
            net = Decimal(booking.attrs.get("net", 0))
            discount_net = Decimal(booking.attrs["discount_net"])
            item_net = net - discount_net
            ret += (item_net * Decimal(booking.attrs.get("vat", 0)) / 100) * count
        return ret

    @property
    def discount_net(self):
        return Decimal(self.order.attrs["cart_discount_net"])

    @property
    def discount_vat(self):
        return Decimal(self.order.attrs["cart_discount_vat"])

    @property
    def shipping_net(self):
        return Decimal(self.order.attrs["shipping_net"])

    @property
    def shipping_vat(self):
        return Decimal(self.order.attrs["shipping_vat"])

    @property
    def shipping(self):
        return Decimal(self.order.attrs["shipping"])

    @property
    def total(self):
        # XXX: use decimal
        total = self.net - self.discount_net + self.vat - self.discount_vat
        return total + self.shipping


@implementer(IBookingData)
class BookingData(OrderState):
    def __init__(self, context, uid=None, booking=None, vendor_uids=[]):
        """Create booking data object by criteria

        :param context: Context to work with
        :type object: Plone or Content instance
        :param uid: Booking uid. XOR with booking
        :type uid: string or uuid.UUID object
        :param booking: Booking record. XOR with uid
        :type booking: souper.soup.Record object
        :param vendor_uids: Vendor uids, used to filter order bookings.
        :type vendor_uids: List of vendor uids as string or uuid.UUID object.
        """
        if not (bool(uid) != bool(booking)):  # ^= xor
            raise ValueError("uid and booing are mutually exclusive")
        if uid and not isinstance(uid, uuid.UUID):
            uid = uuid.UUID(uid)
        vendor_uids = [uuid.UUID(str(vuid)) for vuid in vendor_uids]
        self.context = context
        self._uid = uid
        self._booking = booking
        self.vendor_uids = vendor_uids

    @property
    def uid(self):
        if self._uid:
            return self._uid
        return self.booking.attrs["uid"]

    def reindex(self):
        return

    @property
    def booking(self):
        if self._booking:
            return self._booking
        soup = self.bookings_soup
        query = Eq("uid", self.uid)
        if self.vendor_uids:
            query = query & Any("vendor_uid", self.vendor_uids)
        result = soup.query(query, with_size=True)
        if next(result) != 1:  # first result is length
            return None
        self._booking = next(result)
        return self._booking

    @property
    def order(self):
        # XXX: rename to order_data for less confusion
        return OrderData(
            self.context,
            uid=self.booking.attrs["order_uid"],
            vendor_uids=self.vendor_uids,
        )

    @property
    def state(self):
        return self.booking.attrs["state"]

    @state.setter
    def state(self, value):
        # XXX: currently we need to delete attributes before setting to a new
        #      value in order to persist change. fix in appropriate place.
        booking = self.booking
        self.update_item_stock(booking, booking.attrs["state"], value)
        del booking.attrs["state"]
        booking.attrs["state"] = value
        order = self.order
        del order.order.attrs["state"]
        order.order.attrs["state"] = calculate_order_state(order.bookings)
        self.reindex_bookings([booking])
        self.reindex_order(order.order)

    @property
    def salaried(self):
        return self.booking.attrs["salaried"]

    @salaried.setter
    def salaried(self, value):
        # XXX: currently we need to delete attributes before setting to a new
        #      value in order to persist change. fix in appropriate place.
        booking = self.booking
        del booking.attrs["salaried"]
        booking.attrs["salaried"] = value
        order = self.order
        del order.order.attrs["salaried"]
        order.order.attrs["salaried"] = calculate_order_salaried(
            order.bookings
        )  # noqa
        self.reindex_bookings([booking])
        self.reindex_order(order.order)


class BuyableData(object):
    def __init__(self, context):
        if not IBuyable.providedBy(context):
            raise ValueError("Given context is not IBuyable")
        self.context = context

    def item_ordered(self, state=[]):
        """Return total count buyable item was ordered.
        """
        context = self.context
        bookings_soup = get_bookings_soup(context)
        order_bookings = dict()
        for booking in bookings_soup.query(Eq("buyable_uid", IUUID(context))):
            bookings = order_bookings.setdefault(
                booking.attrs["order_uid"], list()
            )
            bookings.append(booking)
        count = Decimal("0")
        for order_uid, bookings in order_bookings.items():
            for booking in bookings:
                if state and booking.attrs["state"] not in state:
                    continue
                count += booking.attrs["buyable_count"]
        return count


@implementer(IPaymentData)
class PaymentData(object):
    def __init__(self, context):
        self.context = context

    @instance_property
    def order_data(self):
        return OrderData(self.context, uid=self.order_uid)

    @property
    def amount(self):
        amount = "%0.2f" % self.order_data.total
        amount = amount[: amount.index(".")] + amount[amount.index(".") + 1 :]
        return amount

    @property
    def currency(self):
        return self.order_data.currency

    @property
    def description(self):
        order = self.order_data.order
        attrs = order.attrs
        amount = "%s %s" % (
            self.currency,
            str(round(self.order_data.total, 2)),
        )
        description = ", ".join(
            [
                attrs["created"].strftime(DT_FORMAT),
                attrs["personal_data.firstname"],
                attrs["personal_data.lastname"],
                attrs["billing_address.city"],
                safe_encode(amount),
            ]
        )
        return description

    @property
    def ordernumber(self):
        return self.order_data.order.attrs["ordernumber"]

    def uid_for(self, ordernumber):
        soup = get_orders_soup(self.context)
        for order in soup.query(Eq("ordernumber", ordernumber)):
            return str(order.attrs["uid"])

    def data(self, order_uid):
        self.order_uid = order_uid
        return {
            "amount": self.amount,
            "currency": self.currency,
            "description": self.description,
            "ordernumber": self.ordernumber,
        }


def _payment_handling(event, state):
    data = event.data
    order = OrderData(event.context, uid=event.order_uid)
    order.salaried = state
    # XXX: move concrete payment specific changes to bda.plone.payment.
    # Payment may provide a tid attribute to be used here.
    if event.payment.pid == "six_payment":
        order.tid = data["tid"]
    elif event.payment.pid == "stripe_payment":
        order.tid = data["charge_id"]


def payment_success(event):
    _payment_handling(event, workflow.SALARIED_YES)


def payment_failed(event):
    _payment_handling(event, workflow.SALARIED_FAILED)


def booking_update_comment(context, booking_uid, comment):
    booking_data = BookingData(context, uid=booking_uid)
    if booking_data.booking is None:
        raise ValueError("invalid value (booking)")
    booking = booking_data.booking
    booking.attrs["buyable_comment"] = comment
    booking_data.reindex()
