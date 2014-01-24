import uuid
from souper.soup import get_soup
from zope.component.hooks import getSite
from plone.uuid.interfaces import IUUID
from plone.app.uuid.utils import uuidToObject
from bda.plone.orders.common import get_vendor


def fix_bookings_shop_uid(ctx=None):
    """Add shop_uid attribute to booking records.
    """
    portal = getSite()
    soup = get_soup('bda_plone_orders_bookings', portal)
    data = soup.storage.data
    for item in data.values():
        if not 'shop_uid' in item.attrs\
                or not isinstance(item.attrs['shop_uid'], uuid.UUID):
            buyable_uid = item.attrs['buyable_uid']
            obj = uuidToObject(buyable_uid)
            shop = get_vendor(obj)
            shop_uid = uuid.UUID(IUUID(shop))
            item.attrs['shop_uid'] = shop_uid
            print("ADDED shop_uid TO BOOKING %s" % item.attrs['uid'])
    # XXX: rebuild soup catalog and reindex
