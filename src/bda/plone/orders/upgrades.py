from bda.plone.orders import message_factory as _
from bda.plone.orders.common import acquire_vendor_or_shop_root
from bda.plone.orders.common import get_bookings_soup
from bda.plone.orders.common import get_orders_soup
from bda.plone.orders.common import OrderData
from bda.plone.payment import Payments
from decimal import Decimal
from plone.app.uuid.utils import uuidToObject
from plone.uuid.interfaces import IUUID
from zope.component.hooks import getSite

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
        if not 'vendor_uid' in item.attrs\
                or not isinstance(item.attrs['vendor_uid'], uuid.UUID):
            buyable_uid = item.attrs['buyable_uid']
            obj = uuidToObject(buyable_uid)
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
        if not 'vendor_uids' in item.attrs\
                or not isinstance(item.attrs['vendor_uids'], list)\
                or not item.attrs['vendor_uids']:
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
        state = item.attrs.get('state', None)
        salaried = item.attrs.get('salaried', None)
        tid = item.attrs.get('tid', 'none')  # tid default in b.p.payment
        for booking in order_data.bookings:
            # add too booking node
            if 'state' not in booking.attrs:
                booking.attrs['state'] = state
                need_rebuild = True
                logging.info(
                    "Added state {0} to booking {1}".format(
                        state, item.attrs['uid']
                    )
                )
            if 'salaried' not in booking.attrs:
                booking.attrs['salaried'] = salaried
                need_rebuild = True
                logging.info(
                    "Added salaried {0} to booking {1}".format(
                        salaried, item.attrs['uid']
                    )
                )
            if 'tid' not in booking.attrs:
                booking.attrs['tid'] = tid
                need_rebuild = True
                logging.info(
                    "Added tid {0} to booking {1}".format(
                        tid, item.attrs['uid']
                    )
                )
        # now, delete from order node
        if 'state' in item.attrs:
            del item.attrs['state']
        if 'salaried' in item.attrs:
            del item.attrs['salaried']
        if 'tid' in item.attrs:
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
        if not 'cart_discount_net' in item.attrs:
            need_rebuild = True
            item.attrs['cart_discount_net'] = Decimal(0)
            logging.info(
                "Added cart_discount_net to order {0}".format(item.attrs['uid'])
            )
        if not 'cart_discount_vat' in item.attrs:
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
        if not 'discount_net' in item.attrs:
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
        if not 'shipping_method' in item.attrs:
            item.attrs['shipping_method'] = 'unknown'
            logging.info(
                "Added shipping_method {0} to booking {1}".format(
                    'unknown', item.attrs['uid']
                )
            )
        if not 'shipping_label' in item.attrs:
            item.attrs['shipping_label'] = _('unknown', default=u'Unknown')
            logging.info(
                "Added shipping_label {0} to booking {1}".format(
                    'unknown', item.attrs['uid']
                )
            )
        if not 'shipping_description' in item.attrs:
            item.attrs['shipping_description'] = \
                _('unknown', default=u'Unknown')
            logging.info(
                "Added shipping_description {0} to booking {1}".format(
                    'unknown', item.attrs['uid']
                )
            )
        if not 'shipping_net' in item.attrs:
            item.attrs['shipping_net'] = item.attrs['shipping']
            logging.info(
                "Added shipping_net {0} to booking {1}".format(
                    item.attrs['shipping'], item.attrs['uid']
                )
            )
        if not 'shipping_vat' in item.attrs:
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
        if not 'payment_method' in item.attrs:
            continue
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
