from bda.plone.orders.common import get_vendor
from plone.app.uuid.utils import uuidToObject
from plone.uuid.interfaces import IUUID
from souper.soup import get_soup
from zope.component.hooks import getSite

import logging
import uuid

logger = logging.getLogger('bda.plone.orders UPGRADE')


def fix_bookings_shop_uid(ctx=None):
    """Add shop_uid attribute to booking records.
    """
    portal = getSite()
    soup = get_soup('bda_plone_orders_bookings', portal)
    data = soup.storage.data
    need_reindex = False
    for item in data.values():
        if not 'shop_uid' in item.attrs\
                or not isinstance(item.attrs['shop_uid'], uuid.UUID):
            buyable_uid = item.attrs['buyable_uid']
            obj = uuidToObject(buyable_uid)
            shop = get_vendor(obj)
            shop_uid = uuid.UUID(IUUID(shop))
            item.attrs['shop_uid'] = shop_uid
            need_reindex = True
            logging.info(
                "Added shop_uid to booking {0}".format(item.attrs['uid'])
            )
    if need_reindex:
        soup.reindex()
        logging.info("Reindexed bookings souper storage")
