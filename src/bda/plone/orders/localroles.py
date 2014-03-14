from zope.interface import implementer
from plone.app.workflow.interfaces import ISharingPageRole
from bda.plone.orders import permissions
from bda.plone.orders import message_factory as _


@implementer(ISharingPageRole)
class VendorRole(object):
    title = _(u"title_is_vendor", default=u"Is Vendor")
    required_permission = permissions.DelegateVendorRole
