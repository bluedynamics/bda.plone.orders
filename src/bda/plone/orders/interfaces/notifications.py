# -*- coding: utf-8 -*-
from zope.interface import Attribute
from zope.interface import Interface


class INotificationSettings(Interface):
    """Mail notification settings.
    """

    admin_email = Attribute(u"Shop admin email address")
    admin_name = Attribute(u"Shop admin name")


class IItemNotificationText(Interface):
    """Notification text for items in order.
    """

    order_text = Attribute(u"Text sent after successful checkout for item")
    overbook_text = Attribute(
        u"Text sent after successful checkout for item if stock overbooked"
    )


class IGlobalNotificationText(Interface):
    """Notification text per order.
    """

    global_order_text = Attribute(u"Text sent after successful checkout for order")
    global_overbook_text = Attribute(
        u"Text sent after successful checkout for order if stock overbooked"
    )


class IPaymentText(Interface):
    """Payment related order notification text.
    """

    def payment_text(payment):
        """Text sent after successful checkout for payment
        """
