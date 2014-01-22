from zope.interface import Interface


class IOrdersExtensionLayer(Interface):
    """Browser layer for bda.plone.orders
    """


class IVendor(Interface):
    """Provide Vendor relevant information.
    """
