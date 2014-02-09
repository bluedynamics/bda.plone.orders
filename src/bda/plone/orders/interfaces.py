from zope.interface import Interface
from zope.interface import Attribute
from bda.plone.checkout.interfaces import ICheckoutExtensionLayer


class IOrdersExtensionLayer(ICheckoutExtensionLayer):
    """Browser layer for bda.plone.orders
    """


class IVendor(Interface):
    """A Vendor. Used to create isolated areas within one shop for multiple
    vendors.
    """


class INotificationText(Interface):
    """Interface for providing buyable item order notification text.
    """
    order_text = Attribute(u"Text sent after successful checkout for item")

    overbook_text = Attribute(u"Text sent after successful checkout for item "
                              u"if stock overbooked")


class IPaymentText(Interface):
    """Interface for providing payment related order notification text.
    """
    payment_text = Attribute(u"Text sent after successful checkout for payment")
