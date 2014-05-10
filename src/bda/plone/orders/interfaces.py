from bda.plone.checkout.interfaces import ICheckoutExtensionLayer
from bda.plone.discount.interfaces import IDiscountSettingsEnabled
from zope.interface import Attribute
from zope.interface import Interface


STATE_CANCELLED = 'cancelled'
STATE_FINISHED = 'finished'
STATE_MIXED = 'mixed'
STATE_NEW = 'new'
STATE_PROCESSING = 'processing'
STATE_RESERVED = 'reserved'

STATE_TRANSITION_RENEW = 'renew'
STATE_TRANSITION_PROCESS = 'process'
STATE_TRANSITION_FINISH = 'finish'
STATE_TRANSITION_CANCEL = 'cancel'

SALARIED_YES = 'yes'
SALARIED_NO = 'no'
SALARIED_MIXED = 'mixed'
SALARIED_FAILED = 'failed'

SALARIED_TRANSITION_SALARIED = 'mark_salaried'
SALARIED_TRANSITION_OUTSTANDING = 'mark_outstanding'


class IOrdersExtensionLayer(ICheckoutExtensionLayer):
    """Browser layer for bda.plone.orders
    """


class IVendor(IDiscountSettingsEnabled):
    """A Vendor. Used to create isolated areas within one shop for multiple
    vendors.
    """


class ITrading(Interface):
    """Interface for looking up trading related information.
    """

    item_number = Attribute(u"Item Number")

    gtin = Attribute(u"Global Trade Item Number")


class INotificationSettings(Interface):
    """Interface for looking up mail notification settings.
    """

    admin_email = Attribute(u"Shop admin email address")

    admin_name = Attribute(u"Shop admin name")


class IItemNotificationText(Interface):
    """Interface for providing notification text for items in order.
    """

    order_text = Attribute(u"Text sent after successful checkout for item")

    overbook_text = Attribute(
        u"Text sent after successful checkout for item if stock overbooked"
    )


class IGlobalNotificationText(Interface):
    """Interface for providing one notification text per order.
    """

    global_order_text = Attribute(
        u"Text sent after successful checkout for order"
    )

    global_overbook_text = Attribute(
        u"Text sent after successful checkout for order if stock overbooked"
    )


class IPaymentText(Interface):
    """Interface for providing payment related order notification text.
    """

    def payment_text(payment):
        """Text sent after successful checkout for payment
        """


class IDynamicMailTemplateLibrary(Interface):
    """A set of named templates.
    """

    def keys():
        """list names of templates.
        """

    def __getitem__(name):
        """return template by name.
        """


class IDynamicMailTemplateLibraryStorage(IDynamicMailTemplateLibrary):

    def direct_keys():
        """non acquired keys.
        """

    def __setitem__(name, template):
        """store template under a name.
        """

    def __delitem__(name):
        """remove template with this name.
        """
