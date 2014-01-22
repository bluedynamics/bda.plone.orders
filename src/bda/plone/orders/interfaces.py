from bda.plone.checkout.interfaces import ICheckoutExtensionLayer
from zope.interface import (
    Interface,
    Attribute,
)


class IOrdersExtensionLayer(ICheckoutExtensionLayer):
    """Browser layer for bda.plone.orders
    """


class ISubShop(Interface):
    """A sub shop. Used to create multiple shops within a site for mutpliple
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
    text = Attribute(u"Text sent after successful checkout for payment")
