# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from Acquisition import aq_parent
from bda.plone.cart.utils import get_object_by_uid
from bda.plone.orders import permissions
from bda.plone.orders.interfaces.markers import IVendor
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.interfaces import IPloneSiteRoot
from repoze.catalog.query import Any
from repoze.catalog.query import Eq
from souper.soup import get_soup
from zope.deferredimport import deprecated

import logging
import plone.api
import uuid


deprecated(
    "Import from new location 'catalogfactories' instead",
    BookingsCatalogFactory="bda.plone.orders.catalogfactories:BookingsCatalogFactory",
    OrdersCatalogFactory="bda.plone.orders.catalogfactories:OrdersCatalogFactory",
)
deprecated(
    "Import from new location 'checkout' instead",
    OrderCheckoutAdapter="bda.plone.orders.checkout:OrderCheckoutAdapter",
)
deprecated(
    "Import from new location 'datamanager.base' instead",
    OrderState="bda.plone.orders.datamanager.base:BaseState",
    calculate_order_state="bda.plone.orders.datamanager.base:calculate_order_state",
    calculate_order_salaried="bda.plone.orders.datamanager.base:calculate_order_salaried",
)
deprecated(
    "Import from new location 'datamanager.order' instead",
    create_order_number="bda.plone.orders.datamanager.order:create_order_number",
    OrderData="bda.plone.orders.datamanager.order:OrderData",
)
deprecated(
    "Import from new location 'datamanager.booking' instead",
    BookingData="bda.plone.orders.datamanager.booking:BookingData",
    booking_update_comment="bda.plone.orders.datamanager.booking:booking_update_comment",
)
deprecated(
    "Import from new location 'datamanager.buyable' instead",
    BuyableData="bda.plone.orders.datamanager.buyable:BuyableData",
)
deprecated(
    "Import from new location 'datamanager.payment' instead",
    PaymentData="bda.plone.orders.datamanager.payment:PaymentData",
    payment_success="bda.plone.orders.datamanager.payment:payment_success",
    payment_failed="bda.plone.orders.datamanager.payment:payment_failed",
)

logger = logging.getLogger(__name__)


DT_FORMAT = "%d.%m.%Y %H:%M"
DT_FORMAT_SHORT = "%d.%m.%Y"


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
    while not IVendor.providedBy(context) and not IPloneSiteRoot.providedBy(context):
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
