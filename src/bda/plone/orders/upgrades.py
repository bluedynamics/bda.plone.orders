from bda.plone.cart import get_object_by_uid
from bda.plone.orders import message_factory as _
from bda.plone.orders.common import acquire_vendor_or_shop_root
from bda.plone.orders.common import get_bookings_soup
from bda.plone.orders.common import get_orders_soup
from bda.plone.orders.common import OrderData
from bda.plone.orders.interfaces import ITrading
from bda.plone.payment import Payments
from bda.plone.shipping.interfaces import IShippingItem
from decimal import Decimal
from plone.app.uuid.utils import uuidToObject
from plone.uuid.interfaces import IUUID
from zope.component.hooks import getSite
from node.ext.zodb.utils import reset_odict

import logging
import uuid

logger = logging.getLogger('bda.plone.orders UPGRADE')


def fix_bookings_vendor_uid(ctx=None):
    """Add vendor_uid attribute to booking records.
    """
    portal = getSite()
    soup = get_bookings_soup(portal)
    data = soup.storage.data
    need_rebuild = False
    for item in data.values():
        update = False
        try:
            item.attrs['vendor_uid']
            if not isinstance(item.attrs['vendor_uid'], uuid.UUID):
                update = True
        except KeyError:
            update = True
        if not update:
            continue
        buyable_uid = item.attrs['buyable_uid']
        obj = uuidToObject(buyable_uid)
        if not obj:
            shop = acquire_vendor_or_shop_root(portal)
        else:
            shop = acquire_vendor_or_shop_root(obj)
        vendor_uid = uuid.UUID(IUUID(shop))
        item.attrs['vendor_uid'] = vendor_uid
        need_rebuild = True
        logging.info(
            "Added vendor_uid to booking {0}".format(item.attrs['uid'])
        )
    if need_rebuild:
        soup.rebuild()
        logging.info("Rebuilt bookings catalog")


def fix_orders_vendor_uids(ctx=None):
    """Add vendor_uids attribute to order records.
    """
    portal = getSite()
    soup = get_orders_soup(portal)
    data = soup.storage.data
    need_rebuild = False
    for item in data.values():
        update = False
        try:
            item.attrs['vendor_uids']
            if not isinstance(item.attrs['vendor_uids'], list)\
                    or not item.attrs['vendor_uids']:
                update = True
        except KeyError:
            update = True
        if not update:
            continue
        order_data = OrderData(portal, order=item)
        vendor_uids = set()
        for booking in order_data.bookings:
            vendor_uids.add(booking.attrs['vendor_uid'])
        item.attrs['vendor_uids'] = list(vendor_uids)
        need_rebuild = True
        logging.info(
            "Added vendor_uids to order {0}".format(item.attrs['uid'])
        )
    if need_rebuild:
        soup.rebuild()
        logging.info("Rebuilt orders catalog")


def fix_bookings_state_salaried_tid(ctx=None):
    portal = getSite()
    soup = get_orders_soup(portal)
    data = soup.storage.data
    need_rebuild = False
    for item in data.values():
        order_data = OrderData(portal, order=item)
        try:
            state = item.attrs['state']
            state_exists = True
        except KeyError:
            state = None
            state_exists = False
        try:
            salaried = item.attrs['salaried']
            salaried_exists = True
        except KeyError:
            salaried = None
            salaried_exists = False
        try:
            tid = item.attrs['tid']
            tid_exists = True
        except KeyError:
            tid = 'none'  # tid default in b.p.payment
            tid_exists = False
        for booking in order_data.bookings:
            # add too booking node
            try:
                booking.attrs['state']
            except KeyError:
                booking.attrs['state'] = state
                need_rebuild = True
                logging.info(
                    "Added state {0} to booking {1}".format(
                        state, item.attrs['uid']
                    )
                )
            try:
                booking.attrs['salaried']
            except KeyError:
                booking.attrs['salaried'] = salaried
                need_rebuild = True
                logging.info(
                    "Added salaried {0} to booking {1}".format(
                        salaried, item.attrs['uid']
                    )
                )
            try:
                booking.attrs['tid']
            except KeyError:
                booking.attrs['tid'] = tid
                need_rebuild = True
                logging.info(
                    "Added tid {0} to booking {1}".format(
                        tid, item.attrs['uid']
                    )
                )
        # now, delete from order node
        if state_exists:
            del item.attrs['state']
        if salaried_exists:
            del item.attrs['salaried']
        if tid_exists:
            del item.attrs['tid']
    if need_rebuild:
        bookings_soup = get_bookings_soup(portal)
        bookings_soup.rebuild()
        logging.info("Rebuilt bookings catalog")


def fix_discount_attrs(ctx=None):
    portal = getSite()
    # discount attrs on order
    orders_soup = get_orders_soup(portal)
    need_rebuild = False
    data = orders_soup.storage.data
    for item in data.values():
        try:
            item.attrs['cart_discount_net']
        except KeyError:
            need_rebuild = True
            item.attrs['cart_discount_net'] = Decimal(0)
            logging.info(
                "Added cart_discount_net to order {0}".format(item.attrs['uid'])
            )
        try:
            item.attrs['cart_discount_vat']
        except KeyError:
            need_rebuild = True
            item.attrs['cart_discount_vat'] = Decimal(0)
            logging.info(
                "Added cart_discount_vat to order {0}".format(item.attrs['uid'])
            )
    if need_rebuild:
        orders_soup.rebuild()
        logging.info("Rebuilt orders catalog")
    # discount attrs on bookings
    bookings_soup = get_bookings_soup(portal)
    need_rebuild = False
    data = bookings_soup.storage.data
    for item in data.values():
        try:
            item.attrs['discount_net']
        except KeyError:
            need_rebuild = True
            item.attrs['discount_net'] = Decimal(0)
            logging.info(
                "Added discount_net to booking {0}".format(item.attrs['uid'])
            )
    if need_rebuild:
        bookings_soup.rebuild()
        logging.info("Rebuilt bookings catalog")


def fix_shipping_attrs(ctx=None):
    portal = getSite()
    orders_soup = get_orders_soup(portal)
    data = orders_soup.storage.data
    for item in data.values():
        try:
            item.attrs['shipping_method']
        except KeyError:
            item.attrs['shipping_method'] = 'unknown'
            logging.info(
                "Added shipping_method {0} to booking {1}".format(
                    'unknown', item.attrs['uid']
                )
            )
        try:
            item.attrs['shipping_label']
        except KeyError:
            item.attrs['shipping_label'] = _('unknown', default=u'Unknown')
            logging.info(
                "Added shipping_label {0} to booking {1}".format(
                    'unknown', item.attrs['uid']
                )
            )
        try:
            item.attrs['shipping_description']
        except KeyError:
            item.attrs['shipping_description'] = \
                _('unknown', default=u'Unknown')
            logging.info(
                "Added shipping_description {0} to booking {1}".format(
                    'unknown', item.attrs['uid']
                )
            )
        try:
            item.attrs['shipping_net']
        except KeyError:
            item.attrs['shipping_net'] = item.attrs['shipping']
            logging.info(
                "Added shipping_net {0} to booking {1}".format(
                    item.attrs['shipping'], item.attrs['uid']
                )
            )
        try:
            item.attrs['shipping_vat']
        except KeyError:
            item.attrs['shipping_vat'] = Decimal(0)
            logging.info(
                "Added shipping_vat {0} to booking {1}".format(
                    Decimal(0), item.attrs['uid']
                )
            )


def fix_payment_attrs(ctx=None):
    portal = getSite()
    payments = Payments(portal)
    orders_soup = get_orders_soup(portal)
    data = orders_soup.storage.data
    for item in data.values():
        try:
            item.attrs['payment_method']
            item.attrs['payment_label']
            continue
        except KeyError:
            payment_method = item.attrs['payment_selection.payment']
            payment = payments.get(payment_method)
            if payment:
                payment_label = payment.label
            else:
                payment_label = _('unknown', default=u'Unknown')
            item.attrs['payment_method'] = payment_method
            logging.info(
                "Added payment_method {0} to booking {1}".format(
                    payment_method, item.attrs['uid']
                )
            )
            item.attrs['payment_label'] = payment_label
            logging.info(
                "Added payment_label {0} to booking {1}".format(
                    payment_label, item.attrs['uid']
                )
            )


def fix_bookings_shippable(ctx=None):
    portal = getSite()
    soup = get_bookings_soup(portal)
    data = soup.storage.data
    need_rebuild = False
    for booking in data.values():
        try:
            booking.attrs['shippable']
        except KeyError:
            obj = get_object_by_uid(portal, booking.attrs['buyable_uid'])
            shippable = True
            if obj:
                shippable = IShippingItem(obj).shippable
            booking.attrs['shippable'] = shippable
            need_rebuild = True
            logging.info(
                "Added shippable {0} to booking {1}".format(
                    shippable, booking.attrs['uid']
                )
            )
    if need_rebuild:
        bookings_soup = get_bookings_soup(portal)
        bookings_soup.rebuild()
        logging.info("Rebuilt bookings catalog")


def fix_bookings_trading(ctx=None):
    portal = getSite()
    soup = get_bookings_soup(portal)
    data = soup.storage.data
    need_rebuild = False
    for booking in data.values():
        try:
            booking.attrs['item_number']
        except KeyError:
            obj = get_object_by_uid(portal, booking.attrs['buyable_uid'])
            if obj:
                trading = ITrading(obj)
                item_number = trading.item_number
                gtin = trading.gtin
            else:
                item_number = ''
                gtin = ''
            need_rebuild = True
            booking.attrs['item_number'] = item_number
            logging.info(
                "Added item_number {0} to booking {1}".format(
                    item_number, booking.attrs['uid']
                )
            )
            booking.attrs['gtin'] = gtin
            logging.info(
                "Added gtin {0} to booking {1}".format(
                    gtin, booking.attrs['uid']
                )
            )
    if need_rebuild:
        bookings_soup = get_bookings_soup(portal)
        bookings_soup.rebuild()
        logging.info("Rebuilt bookings catalog")


def reset_records(ctx=None):
    ignore_key = lambda x: x.startswith('____')
    portal = getSite()
    soup = get_orders_soup(portal)
    data = soup.storage.data
    for order in data.values():
        reset_odict(order.attrs.storage, ignore_key=ignore_key)
        logging.info(
                "Reset attributes storage on order {0}".format(
                    order.attrs['uid'],
                )
            )
    soup = get_bookings_soup(portal)
    data = soup.storage.data
    for booking in data.values():
        reset_odict(booking.attrs.storage, ignore_key=ignore_key)
        logging.info(
                "Reset attributes storage on booking {0}".format(
                    booking.attrs['uid']
                )
            )
