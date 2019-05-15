# -*- coding: utf-8 -*-
from zope.interface import Attribute
from zope.interface import Interface


class IOrderState(Interface):
    """API to handle states of order and booking"""

    context = Attribute(u"content object context of the state to work with")
    uid = Attribute(u"Unique ID of the state")
    state = Attribute(u"state of the order")
    salaried = Attribute(u"Boolean, true if salaried, else false")

    def update_item_stock(booking, old_state, new_state):
        """Change stock according to transition.
        """

    def increase_stock(booking):
        """Increase stock according to booking information"""

    def decrease_stock(booking):
        """Increase stock according to booking information"""

    def reindex_order(order):
        """newly index given order in storage"""

    def reindex_bookings(bookings):
        """newly index given all given bookings in storage"""


class IOrderData(Interface):
    """API to work with an order"""

    order = Attribute(u"raw order data record")
    bookings = Attribute(u"iterable of raw booking data records")
    currency = Attribute(u"currency valid for the order")
    tid = Attribute(u"")
    net = Attribute(u"net sum of the order")
    vat = Attribute(u"vat sum of the order")
    discount_net = Attribute(u"net part of discount applied")
    discount_vat = Attribute(u"vat part of discount applied")
    shipping = Attribute(u"sum of shipping costs")
    total = Attribute(u"total including all costs")


class IBookingData(Interface):
    """API to work with a booking"""

    uid = Attribute(u"nique ID of the booking")


class IInvoiceSender(Interface):
    """Invoice sender information.
    """

    company = Attribute(u"Sender company name")
    companyadd = Attribute(u"Optional Company additional text line")
    firstname = Attribute(u"Sender first name")
    lastname = Attribute(u"Sender last name")
    street = Attribute(u"Streetg")
    zip = Attribute(u"ZIP")
    city = Attribute(u"City")
    country = Attribute(u"Country")
    phone = Attribute(u"Optional phone number")
    email = Attribute(u"Optional email address")
    web = Attribute(u"Optional web address")
    iban = Attribute(u"Banking connection IBAN")
    bic = Attribute(u"Banking connection BIC")
