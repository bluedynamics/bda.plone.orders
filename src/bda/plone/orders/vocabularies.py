from bda.plone.orders.common import get_all_vendors
from bda.plone.orders.common import get_vendors_for
from bda.plone.orders.common import get_vendor_order_uids_for
from bda.plone.orders.common import get_order
from plone.uuid.interfaces import IUUID
from zope.component.hooks import getSite

import plone.api


def all_vendors_vocab():
    """Vocabulary for all vendor areas by uuid.
    """
    vendors = get_all_vendors()
    vocab = [(IUUID(vendor),
             '{0} ({1})'.format(vendor.Title(), vendor.absolute_url_path()))
             for vendor in vendors]
    return vocab


def vendors_vocab_for(user=None):
    """Vendors vocabulary for given or currently authenticated user.
    """
    vendors = get_vendors_for(user=user)
    vocab = [(IUUID(vendor),
             '{0} ({1})'.format(vendor.Title(), vendor.absolute_url_path()))
             for vendor in vendors]
    return vocab


def customers_vocab_for(user=None):
    """Customers vocabulary for given or currently authenticated user.
    """
    # XXX: expect context as argument
    context = getSite()
    order_uids = get_vendor_order_uids_for(context, user=user)
    res = set(get_order(context, uid).attrs['creator'] for uid in order_uids)
    vocab = []
    for creator in res:
        customer = plone.api.user.get(userid=creator)
        if customer:
            # soft dep on bda.plone.shop
            first = customer.getProperty('firstname', '')
            last = customer.getProperty('lastname', '')
            # fallback
            full = customer.getProperty('fullname', '')
            name = (first or last) and '{0}, {1}'.format(first, last) or full
        else:
            name = creator
        title = name and '{0} ({1})'.format(creator, name) or creator
        vocab.append((creator, title))
    return vocab
