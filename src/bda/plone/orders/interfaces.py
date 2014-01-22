from bda.plone.checkout.interfaces import ICheckoutExtensionLayer
from zope.interface import Interface


class IOrdersExtensionLayer(ICheckoutExtensionLayer):
    """Browser layer for bda.plone.orders
    """


class ISubShop(Interface):
    """A sub shop. Used to create multiple shops within a site for mutpliple
    vendors.
    """
