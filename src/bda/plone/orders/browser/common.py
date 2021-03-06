# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from bda.plone.orders import message_factory as _
from bda.plone.orders import permissions
from bda.plone.orders import vocabularies as vocabs
from bda.plone.orders.common import get_vendor_by_uid
from bda.plone.orders.common import get_vendor_uids_for
from Products.Five import BrowserView
from zope.i18n import translate
from zope.i18nmessageid import Message

import plone.api


###############################################################################
# utils
###############################################################################


def vendors_form_vocab():
    vendors = vocabs.vendors_vocab_for()
    return [("", _("all", default="All"))] + vendors


def customers_form_vocab():
    customers = vocabs.customers_vocab_for()
    return [("", _("all", default="All"))] + customers


def states_form_vocab():
    states = vocabs.state_vocab()
    return [("", _("all", default="All"))] + list(states.items())


def salaried_form_vocab():
    salaried = vocabs.salaried_vocab()
    return [("", _("all", default="All"))] + list(salaried.items())


class Translate(object):
    def __init__(self, request):
        self.request = request

    def __call__(self, msg):
        if not isinstance(msg, Message):
            return msg
        return translate(msg, context=self.request)


class Transition(BrowserView):
    dropdown = None

    @property
    def vendor_uids(self):
        vendor_uid = self.request.form.get("vendor", "")
        if vendor_uid:
            vendor_uids = [vendor_uid]
            vendor = get_vendor_by_uid(self.context, vendor_uid)
            user = plone.api.user.get_current()
            if not user.checkPermission(permissions.ModifyOrders, vendor):
                raise Unauthorized
        else:
            vendor_uids = get_vendor_uids_for()
            if not vendor_uids:
                raise Unauthorized
        return vendor_uids

    def __call__(self):
        uid = self.request["uid"]
        transition = self.request["transition"]
        vendor_uids = self.vendor_uids
        record = self.do_transition(uid, transition, vendor_uids)
        return self.dropdown(self.context, self.request, record).render()

    def do_transition(self, uid, transition, vendor_uids):
        raise NotImplementedError()


###############################################################################
# content view base classes
###############################################################################


class ContentTemplateView(BrowserView):
    """View mixin for rendering content from dedicated template.
    """

    content_template = None

    def render_content(self):
        return self.content_template(self)
