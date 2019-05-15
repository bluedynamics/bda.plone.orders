# -*- coding: utf-8 -*-
from bda.plone.cart.interfaces import ICartItem
from bda.plone.checkout.interfaces import ICheckoutExtensionLayer
from bda.plone.discount.interfaces import IDiscountSettingsEnabled


class IBuyable(ICartItem, IDiscountSettingsEnabled):
    """Marker for buyable item.

    Item is buyable.
    """


class IOrdersExtensionLayer(ICheckoutExtensionLayer):
    """Browser layer request marker indicating bda.plone.orders is installed.
    """


class IVendor(IDiscountSettingsEnabled):
    """A Vendor marker for containers.

    Used to create isolated areas within one shop for multiple vendors.
    """
