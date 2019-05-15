# -*- coding: utf-8 -*-
from bda.plone.orders import interfaces as ifaces
from bda.plone.orders import message_factory as _
from bda.plone.orders.common import get_all_vendors
from bda.plone.orders.common import get_order
from bda.plone.orders.common import get_vendor_order_uids_for
from bda.plone.orders.common import get_vendors_for
from plone.i18n.normalizer.base import baseNormalize
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.utils import safe_unicode
from zope.component.hooks import getSite

import plone.api


def state_vocab():
    vocab = {
        ifaces.STATE_NEW: _('new', default=u'New'),
        ifaces.STATE_PROCESSING: _('processing', default=u'Processing'),
        ifaces.STATE_FINISHED: _('finished', default=u'Finished'),
        ifaces.STATE_CANCELLED: _('cancelled', default=u'Cancelled'),
        ifaces.STATE_RESERVED: _('reserved', default=u'Reserved'),
        ifaces.STATE_MIXED: _('mixed', default=u'Mixed'),
    }
    return vocab


def state_transitions_vocab():
    vocab = {
        ifaces.STATE_TRANSITION_RENEW: _('renew', default=u'Renew'),
        ifaces.STATE_TRANSITION_PROCESS: _('process', default=u'Process'),
        ifaces.STATE_TRANSITION_FINISH: _('finish', default=u'Finish'),
        ifaces.STATE_TRANSITION_CANCEL: _('cancel', default=u'Cancel'),
    }
    return vocab


def salaried_vocab():
    vocab = {
        ifaces.SALARIED_YES: _('yes', default=u'Yes'),
        ifaces.SALARIED_NO: _('no', default=u'No'),
        ifaces.SALARIED_FAILED: _('failed', default=u'Failed'),
        ifaces.SALARIED_MIXED: _('mixed', default=u'Mixed'),
    }
    return vocab


def salaried_transitions_vocab():
    vocab = {
        ifaces.SALARIED_TRANSITION_SALARIED: _(
            'mark_salaried', default=u'Mark salaried'
        ),
        ifaces.SALARIED_TRANSITION_OUTSTANDING: _(
            'mark_outstanding', default=u'Mark outstanding'
        ),
    }
    return vocab


def groups_vocab():
    """
    used for grouping the bookings table
    """
    vocab = {
        'email': _('email', default=u'Email'),
        'buyable': _('buyable', default=u'Buyable'),
    }
    return vocab


def all_vendors_vocab():
    """Vocabulary for all vendor areas by uuid.
    """
    vendors = get_all_vendors()
    vocab = [
        (
            IUUID(vendor),
            u'{0} ({1})'.format(
                safe_unicode(vendor.Title()), vendor.absolute_url_path()
            ),
        )
        for vendor in vendors
    ]
    return vocab


def vendors_vocab_for(user=None):
    """Vendors vocabulary for given or currently authenticated user.
    """
    vendors = get_vendors_for(user=user)
    vocab = [
        (
            IUUID(vendor),
            u'{0} ({1})'.format(
                safe_unicode(vendor.Title()), vendor.absolute_url_path()
            ),
        )
        for vendor in vendors
    ]
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
        if not creator:
            # Development edge case: creator might be None
            continue
        customer = plone.api.user.get(userid=creator)

        email = None
        name = None
        if customer:
            # soft dep on bda.plone.shop
            first = safe_unicode(customer.getProperty('firstname', ''))
            last = safe_unicode(customer.getProperty('lastname', ''))
            email = safe_unicode(customer.getProperty('email', ''))
            # fallback
            full = safe_unicode(customer.getProperty('fullname', ''))
            name = u'{0}, {1}'.format(last, first) if (first or last) else full

        if email and name:
            title = u'{0} ({1}) - {2}'.format(name, creator, email)
        else:
            title = creator
        vocab.append((creator, title))

    # Sort the vocab by title, normalized like sortable_title
    vocab = sorted(vocab, key=lambda x: baseNormalize(x[1]).lower())

    return vocab
