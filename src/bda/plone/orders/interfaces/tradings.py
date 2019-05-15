# -*- coding: utf-8 -*-
from zope.interface import Attribute
from zope.interface import Interface


class ITrading(Interface):
    """Trading related information.
    """

    item_number = Attribute(u"Item Number")
    gtin = Attribute(u"Global Trade Item Number")
