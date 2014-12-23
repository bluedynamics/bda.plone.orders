# -*- coding: utf-8 -*-
from bda.plone.orders import message_factory as _
from bda.plone.orders import permissions
from bda.plone.orders.interfaces import IVendor
from plone.app.workflow.interfaces import ISharingPageRole
from zope.interface import implementer


@implementer(ISharingPageRole)
class VendorRole(object):
    title = _(u"title_vendor_role", default=u"Can Sell")
    required_permission = permissions.DelegateVendorRole
    required_interface = IVendor


@implementer(ISharingPageRole)
class CustomerRole(object):
    title = _(u"title_customer_role", default=u"Can Buy")
    required_permission = permissions.DelegateCustomerRole
    required_interface = None
