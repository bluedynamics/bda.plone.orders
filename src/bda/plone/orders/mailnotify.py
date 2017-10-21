# -*- coding: utf-8 -*-
from Products.CMFPlone.utils import safe_unicode
from bda.plone.cart import ascur
from bda.plone.cart import get_catalog_brain
from bda.plone.checkout.interfaces import ICheckoutEvent
from bda.plone.checkout.interfaces import ICheckoutSettings
from bda.plone.orders import get_country_name
from bda.plone.orders import interfaces as ifaces
from bda.plone.orders import message_factory as _
from bda.plone.orders import vocabularies as vocabs
from bda.plone.orders.common import DT_FORMAT
from bda.plone.orders.common import OrderData
from bda.plone.orders.interfaces import IGlobalNotificationText
from bda.plone.orders.interfaces import IItemNotificationText
from bda.plone.orders.interfaces import INotificationSettings
from bda.plone.orders.interfaces import IPaymentText
from bda.plone.orders.mailtemplates import get_booking_cancelled_templates
from bda.plone.orders.mailtemplates import get_booking_reserved_to_ordered_templates  # noqa
from bda.plone.orders.mailtemplates import get_order_templates
from bda.plone.orders.mailtemplates import get_reservation_templates
from bda.plone.orders.mailtemplates import get_stock_threshold_reached_templates  # noqa
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from plone import api
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.i18n import translate
import logging
import textwrap


logger = logging.getLogger('bda.plone.orders')


NOTIFICATIONS = {}


POSSIBLE_TEMPLATE_CALLBACKS = [
    'booking_cancelled_title',
    'booking_reserved_to_ordered_title',
    'global_text',
    'item_listing',
    'reserved_item_listing',
    'order_summary',
    'payment_text',
    'stock_threshold_reached_text',
    'delivery_address',
]


def get_order_uid(event):
    uid = None
    if ICheckoutEvent.providedBy(event):
        uid = event.uid
    else:
        uid = event.order_uid
    return uid


def _indent(text, ind=5, width=80):
    """Helper indents text.
    """
    wrapped = textwrap.fill(
        safe_unicode(text),
        width,
        initial_indent=ind * u' '
    )
    return wrapped


def _process_template_cb(name, tpls, args, context, order_data):
    """Process template callback.

    The result of the template callback gets written to args.
    """
    cb_name = u'{0:s}_cb'.format(name)
    if cb_name in tpls:
        args[name] = tpls[cb_name](context, order_data)


###############################################################################
# mail notification related data exraction
###############################################################################

def order_item_data(context, booking):
    """Extract data for one listing item.
    """
    data = dict()
    data['title'] = safe_unicode(booking.attrs['title'])
    item_number = u''
    if booking.attrs['item_number']:
        item_number = u' ({0})'.format(
            safe_unicode(booking.attrs['item_number']))
    data['item_number'] = item_number
    data['comment'] = safe_unicode(booking.attrs['buyable_comment'])
    data['currency'] = safe_unicode(booking.attrs['currency'])
    data['buyable_count'] = booking.attrs['buyable_count']
    data['net'] = booking.attrs['net']
    data['discount_net'] = float(booking.attrs['discount_net'])
    data['state'] = state = safe_unicode(booking.attrs.get('state'))
    brain = get_catalog_brain(context, booking.attrs['buyable_uid'])
    buyable = brain.getObject()
    notificationtext = IItemNotificationText(buyable)
    text = None
    if state == ifaces.STATE_RESERVED:
        text = notificationtext.overbook_text
    elif state == ifaces.STATE_NEW:
        text = notificationtext.order_text
    data['notification'] = text
    return data


default_include_booking_states=(
    ifaces.STATE_FINISHED,
    ifaces.STATE_NEW,
    ifaces.STATE_PROCESSING
)

def order_items_data(context, order_data,
                     include_booking_states=default_include_booking_states):
    """Extract item listing data.
    """
    data = list()
    for booking in order_data.bookings:
        if booking.attrs.get('state') not in include_booking_states:
            continue
        data.append(order_item_data(context, booking))
    return data


def order_summary_data(order_data):
    """Extract data for order summary.
    """
    data = dict()
    data['currency'] = order_data.currency
    cart_net = order_data.net
    data['cart_net'] = cart_net
    cart_vat = order_data.vat
    data['cart_vat'] = cart_vat
    discount_net = order_data.discount_net
    data['discount_net'] = discount_net
    discount_vat = order_data.discount_vat
    data['discount_vat'] = discount_vat
    discount_total = discount_net + discount_vat
    data['discount_total'] = discount_total
    attrs = order_data.order.attrs
    data['shipping_label'] = attrs['shipping_label']
    data['shipping_description'] = attrs['shipping_description']
    shipping_net = order_data.shipping_net
    data['shipping_net'] = shipping_net
    shipping_vat = order_data.shipping_vat
    data['shipping_vat'] = shipping_vat
    shipping_total = shipping_net + shipping_vat
    data['shipping_total'] = shipping_total
    cart_total = order_data.total
    data['cart_total'] = cart_total
    return data


def order_payment_data(order_data):
    data = dict()
    data['payment_method'] = payment = order_data.order.attrs['payment_method']
    data['payment_text'] = IPaymentText(getSite()).payment_text(payment)
    return data


def order_notifications(context, order_data):
    order_state = order_data.state
    notifications = set()
    for booking in order_data.bookings:
        brain = get_catalog_brain(context, booking.attrs['buyable_uid'])
        buyable = brain.getObject()
        notificationtext = IGlobalNotificationText(buyable)
        if order_state in (ifaces.STATE_RESERVED, ifaces.STATE_MIXED):
            # XXX: might need custom text for MIXED state
            text = notificationtext.global_overbook_text
            if text:
                notifications.add(text)
        elif order_state == ifaces.STATE_NEW:
            text = notificationtext.global_order_text
            if text:
                notifications.add(text)
    return list(notifications)


def general_order_data(context, order_data):
    lang = context.restrictedTraverse('@@plone_portal_state').language()
    attrs = order_data.order.attrs
    data = dict(
        (safe_unicode(key), safe_unicode(value))
        for (key, value) in attrs.items()
    )
    data['portal_url'] = getSite().absolute_url()
    data['date'] = attrs['created'].strftime(DT_FORMAT)
    data['salutation'] = translate(
        attrs['personal_data.gender'],
        domain='bda.plone.checkout',
        target_language=lang
    )
    if data.get('billing_address.country', None):
        data['billing_address.country'] = \
            get_country_name(
                data['billing_address.country'],
                lang=lang
            )
    if data.get('delivery_address.country', None):
        data['delivery_address.country'] = \
            get_country_name(
                data['delivery_address.country'],
                lang=lang
            )
    return data


###############################################################################
# mail notification
###############################################################################

class MailNotify(object):
    """Mail notifyer.
    """

    def __init__(self, context):
        self.context = context
        self.settings = INotificationSettings(self.context)

    def create_multipart_message(subject, from_, to, text, html):
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = from_
        message['To'] = to
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        message.attach(MIMEText(text, 'plain'))
        message.attach(MIMEText(html, 'html'))
        return message

    def send(self, subject, receiver, text, html=None):
        shop_manager_address = self.settings.admin_email
        if not shop_manager_address:
            raise ValueError('Shop manager address is missing in settings.')
        shop_manager_name = self.settings.admin_name
        if shop_manager_name:
            from_name = shop_manager_name
            mailfrom = formataddr((from_name, shop_manager_address))
        else:
            mailfrom = shop_manager_address
        if html is None:
            message = text
        else:
            message = self.create_multipart_message(
                subject,
                mailfrom,
                receiver,
                text,
                html
            )
        api.portal.send_email(
            recipient=receiver,
            sender=mailfrom,
            subject=subject,
            body=message,
        )


def create_text_mail_body(context, order_data, templates):
    """Creates a rendered mail body

    context
        Some object in Plone which can be used as a context to acquire from.

    order_data
        Order-data instance.

    templates
        Dict with a bunch of cbs and the body template itself.
    """
    arguments = general_order_data(context, order_data)
    for name in POSSIBLE_TEMPLATE_CALLBACKS:
        _process_template_cb(
            name,
            templates,
            arguments,
            context,
            order_data
        )
    return templates['body'] % arguments


def create_html_mail_body(context, template_name, template_data):
    """Creates a rendered mail body

    context
        Some object in Plone which can be used as a context to acquire from.

    template_name
        HTML template name as string.

    template_data
        Dict containing data passed to template.
    """
    return None


def do_notify(context, order_data, receiver,
              templates, template_name, template_data):
    """Do mail notification.
    """
    attrs = order_data.order.attrs
    subject = templates['subject'] % attrs['ordernumber']
    text = create_text_mail_body(context, order_data, templates)
    html = create_html_mail_body(context, template_name, template_data)
    mail_notify = MailNotify(context)
    try:
        mail_notify.send(subject, receiver, text, html=html)
    except Exception:
        msg = translate(
            _('email_sending_failed',
              default=u'Failed to send notification to ${receiver}',
              mapping={'receiver': receiver}))
        api.portal.show_message(message=msg, request=context.REQUEST)
        logger.exception("Email could not be sent.")


def do_notify_customer(context, order_data, templates,
                       template_name, template_data):
    customer_address = order_data.order.attrs['personal_data.email']
    do_notify(
        context,
        order_data,
        customer_address,
        templates,
        template_name,
        template_data
    )


def do_notify_shopmanager(context, order_data, templates,
                          template_name, template_data):
    shop_manager_address = INotificationSettings(context).admin_email
    do_notify(
        context,
        order_data,
        shop_manager_address,
        templates,
        template_name,
        template_data
    )


###############################################################################
# order success
###############################################################################

# template callbacks and helpers ##############################################

def create_order_listing_item(item_data):
    """Create text for one item in order.
    """
    # count
    text = u'{:4f}'.format(item_data['buyable_count'])
    # title
    title = item_data['title']
    comment = item_data['comment']
    if comment:
        title = u'{} ({})'.format(title, comment)
    text = u'{} {}'.format(text, title)
    # item number
    item_number = item_data['item_number']
    if item_number:
        text = u'{} {}'.format(text, item_number)
    # state
    state_text = u''
    if item_data['state'] == ifaces.STATE_RESERVED:
        state_text = u'({})'.format(vocabs.state_vocab()[item_data['state']])
    if state_text:
        text = u'{} {}'.format(text, state_text)
    # price
    currency = item_data['currency']
    net = item_data['net']
    discount_net = item_data['discount_net']
    if discount_net:
        net = net - discount_net
    text = u'{} {} {:0.2f}'.format(text, currency, net)
    # notification text
    notification = item_data['notification']
    if notification:
        return u'\n'.join([text, _indent(notification)])
    return text


def create_order_listing(context, order_data,
                         include_booking_states=default_include_booking_states):
    """Create item listing text for notification mail.
    """
    items = []
    items_data = order_items_data(
        context,
        order_data,
        include_booking_states=include_booking_states
    )
    for item_data in items_data:
        items.append(create_order_listing_item(item_data))
    return u'\n'.join(items)


def create_reserved_order_listing(context, order_data):
    """Create item listing text for notification mail containing reserved items
    of this order.
    """
    return create_order_listing(
        context,
        order_data,
        include_booking_states=(ifaces.STATE_RESERVED,)
    )


def create_order_summary(context, order_data):
    """Create cart summary text for notification mail.
    """
    # no costs at all
    if not order_data.total:
        return u''
    lines = []
    request = getRequest()
    summary_data = order_summary_data(order_data)
    # cart net and vat
    if summary_data['cart_net']:
        # cart net
        lines.append(translate(_(
            'order_summary_cart_net',
            default=u'Net: ${value} ${currency}',
            mapping={
                'value': ascur(summary_data['cart_net']),
                'currency': summary_data['currency'],
            }), context=request))
        # cart vat
        lines.append(translate(_(
            'order_summary_cart_vat',
            default=u'VAT: ${value} ${currency}',
            mapping={
                'value': ascur(summary_data['cart_vat']),
                'currency': summary_data['currency'],
            }), context=request))
    # cart discount
    if summary_data['discount_net']:
        # discount net
        lines.append(translate(_(
            'order_summary_discount_net',
            default=u'Discount Net: ${value} ${currency}',
            mapping={
                'value': ascur(summary_data['discount_net']),
                'currency': summary_data['currency'],
            }), context=request))
        # discount vat
        lines.append(translate(_(
            'order_summary_discount_vat',
            default=u'Discount VAT: ${value} ${currency}',
            mapping={
                'value': ascur(summary_data['discount_vat']),
                'currency': summary_data['currency'],
            }), context=request))
        # discount total
        lines.append(translate(_(
            'order_summary_discount_total',
            default=u'Discount Total: ${value} ${currency}',
            mapping={
                'value': ascur(summary_data['discount_total']),
                'currency': summary_data['currency'],
            }), context=request))
    # shipping costs
    if summary_data['shipping_net']:
        # shiping label
        lines.append(translate(_(
            'order_summary_shipping_label',
            default=u'Shipping: ${label}',
            mapping={
                'label': translate(
                    summary_data['shipping_label'], context=request),
            }), context=request))
        # shiping description
        lines.append(translate(
            summary_data['shipping_description'], context=request))
        # shiping net
        lines.append(translate(_(
            'order_summary_shipping_net',
            default=u'Shipping Net: ${value} ${currency}',
            mapping={
                'value': ascur(summary_data['shipping_net']),
                'currency': summary_data['currency'],
            }), context=request))
        # shiping vat
        lines.append(translate(_(
            'order_summary_shipping_vat',
            default=u'Shipping VAT: ${value} ${currency}',
            mapping={
                'value': ascur(summary_data['shipping_vat']),
                'currency': summary_data['currency'],
            }), context=request))
        # shiping total
        lines.append(translate(_(
            'order_summary_shipping_total',
            default=u'Shipping Total: ${value} ${currency}',
            mapping={
                'value': ascur(summary_data['shipping_total']),
                'currency': summary_data['currency'],
            }), context=request))
    # cart total
    lines.append(translate(_(
        'order_summary_cart_total',
        default=u'Total: ${value} ${currency}',
        mapping={
            'value': ascur(summary_data['cart_total']),
            'currency': summary_data['currency'],
        }), context=request))
    summary_title = translate(
        _('order_summary_label', default=u'Summary:'), context=request)
    summary_text = u'\n'.join(lines)
    return u'\n{summary_title}\n{summary_text}\n'.format(
        summary_title=summary_title,
        summary_text=summary_text
    )


def create_global_text(context, order_data):
    global_text = u'\n\n'.join(order_notifications(context, order_data))
    if global_text.strip():
        return u'\n\n{global_text}\n'.format(global_text=global_text.strip())
    return u''


def create_payment_text(context, order_data):
    payment_text = order_payment_data(order_data)['payment_text']
    if payment_text.strip():
        return u'\n\n{payment_text}\n'.format(payment_text=payment_text.strip())  # noqa
    return u''


def create_delivery_address(context, order_data):
    if order_data.order.attrs['delivery_address.alternative_delivery']:
        templates = get_order_templates(context)
        delivery_address_template = templates['delivery_address']
        arguments = general_order_data(context, order_data)
        return delivery_address_template % arguments
    return u''

# event handling ##############################################################

def dispatch_notify_order_success(event):
    for func in NOTIFICATIONS['order_success']:
        func(event)

# notification ##############################################################

def notify_order_success(event, who=None):
    """Send notification mail after order succeeded.
    """
    if who not in ['customer', 'shopmanager']:
        raise ValueError(
            'kw "who" mus be one out of ("customer", "shopmanager")'
        )
    order_data = OrderData(event.context, uid=get_order_uid(event))
    templates = dict()
    state = order_data.state
    if state in (ifaces.STATE_RESERVED, ifaces.STATE_MIXED):
        templates.update(get_reservation_templates(event.context))
        templates['reserved_item_listing_cb'] = create_reserved_order_listing
    else:
        templates.update(get_order_templates(event.context))
    templates['item_listing_cb'] = create_order_listing
    templates['order_summary_cb'] = create_order_summary
    templates['global_text_cb'] = create_global_text
    templates['payment_text_cb'] = create_payment_text
    templates['delivery_address_cb'] = create_delivery_address
    template_name = 'order_success'
    template_data = dict()
    template_data['order'] = general_order_data(event.context, order_data)
    template_data['items'] = order_items_data(event.context, order_data)
    template_data['reserved_items'] = order_items_data(
        event.context, order_data,
        include_booking_states=(ifaces.STATE_RESERVED,))
    template_data['summary'] = order_summary_data(order_data)
    template_data['payment'] = order_payment_data(order_data)
    template_data['notifications'] = order_notifications(
        event.context, order_data)
    if who == "customer":
        do_notify_customer(
            event.context, order_data, templates, template_name, template_data)
    else:
        do_notify_shopmanager(
            event.context, order_data, templates, template_name, template_data)


def notify_order_success_customer(event):
    notify_order_success(event, who="customer")


def notify_order_success_shopmanager(event):
    notify_order_success(event, who="shopmanager")


NOTIFICATIONS['order_success'] = []
NOTIFICATIONS['order_success'].append(notify_order_success_customer)
NOTIFICATIONS['order_success'].append(notify_order_success_shopmanager)


###############################################################################
# checkout success
###############################################################################

def dispatch_notify_checkout_success(event):
    for func in NOTIFICATIONS['checkout_success']:
        func(event)


def notify_checkout_success_customer(event):
    """Send notification mail after checkout succeed.
    """
    # if skip payment, do notification
    checkout_settings = ICheckoutSettings(event.context)
    if checkout_settings.skip_payment(get_order_uid(event)):
        notify_order_success(event, who="customer")


def notify_checkout_success_shopmanager(event):
    """Send notification mail after checkout succeed.
    """
    # if skip payment, do notification
    checkout_settings = ICheckoutSettings(event.context)
    if checkout_settings.skip_payment(get_order_uid(event)):
        notify_order_success(event, who="shopmanager")


NOTIFICATIONS['checkout_success'] = []
NOTIFICATIONS['checkout_success'].append(notify_checkout_success_customer)
NOTIFICATIONS['checkout_success'].append(notify_checkout_success_shopmanager)


###############################################################################
# payment success
###############################################################################

def dispatch_notify_payment_success(event):
    for func in NOTIFICATIONS['payment_success']:
        func(event)


def notify_payment_success_customer(event):
    """Send notification mail after payment succeed.
    """
    notify_order_success(event, who="customer")


def notify_payment_success_shopmanager(event):
    """Send notification mail after payment succeed.
    """
    notify_order_success(event, who="shopmanager")


NOTIFICATIONS['payment_success'] = []
NOTIFICATIONS['payment_success'].append(notify_payment_success_customer)
NOTIFICATIONS['payment_success'].append(notify_payment_success_shopmanager)


###############################################################################
# booking cancelled
###############################################################################

BOOKING_CANCELLED_TITLE_ATTRIBUTE = 'title'


def dispatch_notify_booking_cancelled(event):
    for func in NOTIFICATIONS['booking_cancelled']:
        func(event)


class BookingCancelledTitleCB(object):

    def __init__(self, event):
        self.event = event

    def __call__(self, *args):
        return self.event.booking_attrs[BOOKING_CANCELLED_TITLE_ATTRIBUTE]


def notify_booking_cancelled(event, who=None):
    """Send notification mail after booking was cancelled.
    """
    order_data = OrderData(event.context, uid=get_order_uid(event))
    templates = dict()
    templates.update(get_booking_cancelled_templates(event.context))
    booking_cancelled_title = BookingCancelledTitleCB(event)
    templates['booking_cancelled_title_cb'] = booking_cancelled_title
    template_name = 'booking_cancelled'
    template_data = dict()
    template_data['order'] = general_order_data(event.context, order_data)
    template_data['booking'] = dict()
    template_data['booking']['title'] = booking_cancelled_title
    if who == "customer":
        do_notify_customer(
            event.context, order_data, templates, template_name, template_data)
    elif who == 'shopmanager':
        do_notify_shopmanager(
            event.context, order_data, templates, template_name, template_data)
    else:
        raise ValueError(
            'kw "who" mus be one out of ("customer", "shopmanager")'
        )


def notify_booking_cancelled_customer(event):
    notify_booking_cancelled(event, who="customer")


def notify_booking_cancelled_shopmanager(event):
    notify_booking_cancelled(event, who="shopmanager")


NOTIFICATIONS['booking_cancelled'] = []
NOTIFICATIONS['booking_cancelled'].append(notify_booking_cancelled_customer)
NOTIFICATIONS['booking_cancelled'].append(notify_booking_cancelled_shopmanager)


###############################################################################
# booking reserved to ordered
###############################################################################

def dispatch_notify_booking_reserved_to_ordered(event):
    for func in NOTIFICATIONS['booking_reserved_to_ordered']:
        func(event)


BookingReservedToOrderedTitleCB = BookingCancelledTitleCB


def notify_booking_reserved_to_ordered(event, who=None):
    """Send notification mail after booking was changed from reserved to ordered.
    """
    order_data = OrderData(event.context, uid=get_order_uid(event))
    templates = dict()
    templates.update(get_booking_reserved_to_ordered_templates(event.context))
    booking_reserved_to_ordered_title = BookingReservedToOrderedTitleCB(event)
    templates['booking_reserved_to_ordered_title_cb'] = booking_reserved_to_ordered_title  # noqa
    template_name = 'booking_reserved_to_ordered'
    template_data = dict()
    template_data['order'] = general_order_data(event.context, order_data)
    template_data['booking'] = dict()
    template_data['booking']['title'] = booking_reserved_to_ordered_title
    if who == "customer":
        do_notify_customer(
            event.context, order_data, templates, template_name, template_data)
    elif who == 'shopmanager':
        do_notify_shopmanager(
            event.context, order_data, templates, template_name, template_data)
    else:
        raise ValueError(
            'kw "who" mus be one out of ("customer", "shopmanager")'
        )


def notify_booking_reserved_to_ordered_customer(event):
    notify_booking_reserved_to_ordered(event, who="customer")


def notify_booking_reserved_to_ordered_shopmanager(event):
    notify_booking_reserved_to_ordered(event, who="shopmanager")


NOTIFICATIONS['booking_reserved_to_ordered'] = []
NOTIFICATIONS['booking_reserved_to_ordered'].append(notify_booking_reserved_to_ordered_customer)  # noqa
NOTIFICATIONS['booking_reserved_to_ordered'].append(notify_booking_reserved_to_ordered_shopmanager)  # noqa


###############################################################################
# stock threshold reached
###############################################################################

def dispatch_notify_stock_threshold_reached(event):
    for func in NOTIFICATIONS['stock_threshold_reached']:
        func(event)


class StockThresholdReachedCB(object):

    def __init__(self, event):
        self.event = event

    def __call__(self, *args):
        text = ''
        items = self.event.stock_threshold_reached_items
        for item_attrs in items:
            title = item_attrs['title']
            remaining = item_attrs['remaining_stock_available']
            text += u'{0} (Remaining stock: {1})\n'.format(title, remaining)
        return text


def notify_stock_threshold_reached(event):
    """Send notification mail when item is getting out of stock.
    """
    order_data = OrderData(event.context, uid=get_order_uid(event))
    templates = dict()
    templates.update(get_stock_threshold_reached_templates(event.context))
    templates['stock_threshold_reached_text_cb'] = \
        StockThresholdReachedCB(event)
    template_name = 'stock_threshold_reached'
    template_data = dict()
    template_data['order'] = general_order_data(event.context, order_data)
    template_data['items'] = event.stock_threshold_reached_items
    do_notify_shopmanager(
        event.context, order_data, templates, template_name, template_data)


NOTIFICATIONS['stock_threshold_reached'] = []
NOTIFICATIONS['stock_threshold_reached'].append(notify_stock_threshold_reached)
