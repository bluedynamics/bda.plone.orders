from bda.plone.orders.common import acquire_vendor_or_shop_root
from bda.plone.orders.common import get_bookings_soup
from bda.plone.orders.common import get_orders_soup
from bda.plone.orders.common import OrderData
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
    need_reindex = False
    for item in data.values():
        if not 'vendor_uid' in item.attrs\
                or not isinstance(item.attrs['vendor_uid'], uuid.UUID):
            buyable_uid = item.attrs['buyable_uid']
            obj = uuidToObject(buyable_uid)
            shop = acquire_vendor_or_shop_root(obj)
            vendor_uid = uuid.UUID(IUUID(shop))
            item.attrs['vendor_uid'] = vendor_uid
            need_reindex = True
            logging.info(
                "Added vendor_uid to booking {0}".format(item.attrs['uid'])
            )
    if need_reindex:
        soup.reindex()
        logging.info("Reindexed bookings souper storage")


def fix_orders_vendor_uids(ctx=None):
    """Add vendor_uids attribute to order records.
    """
    portal = getSite()
    soup = get_bookings_soup(portal)
    data = soup.storage.data
    need_reindex = False
    for item in data.values():
        if not 'vendor_uids' in item.attrs\
                or not isinstance(item.attrs['vendor_uids'], list):
            order_data = OrderData(order=item)
            vendor_uids = set()
            for booking in order_data.bookings:
                vendor_uids.add(booking.attrs['vendor_uid'])
            item.attrs['vendor_uids'] = list(vendor_uids)
            need_reindex = True
            logging.info(
                "Added vendor_uids to order {0}".format(item.attrs['uid'])
            )
    if need_reindex:
        soup.reindex()
        logging.info("Reindexed orders souper storage")
