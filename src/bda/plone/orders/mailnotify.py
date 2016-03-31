# -*- coding: utf-8 -*-
from Products.CMFPlone.utils import safe_unicode
from bda.plone.cart import ascur
from bda.plone.cart import get_catalog_brain
from bda.plone.cart import get_object_by_uid
from bda.plone.checkout.interfaces import ICheckoutEvent
from bda.plone.checkout.interfaces import ICheckoutSettings
from bda.plone.orders import interfaces as ifaces
from bda.plone.orders import message_factory as _
from bda.plone.orders import safe_encode
from bda.plone.orders import vocabularies as vocabs
from bda.plone.orders.common import DT_FORMAT
from bda.plone.orders.common import OrderData
from bda.plone.orders.interfaces import IBookingCancelledEvent
from bda.plone.orders.interfaces import IStockThresholdReached
from bda.plone.orders.interfaces import IGlobalNotificationText
from bda.plone.orders.interfaces import IItemNotificationText
from bda.plone.orders.interfaces import INotificationSettings
from bda.plone.orders.interfaces import IPaymentText
from bda.plone.orders.mailtemplates import get_booking_cancelled_templates
from bda.plone.orders.mailtemplates import get_order_templates
from bda.plone.orders.mailtemplates import get_reservation_templates
from bda.plone.orders.mailtemplates import get_stock_threshold_reached_templates
from bda.plone.payment.interfaces import IPaymentEvent
from email.utils import formataddr
from plone import api
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.i18n import translate

import logging
import textwrap

logger = logging.getLogger('bda.plone.orders')

NOTIFICATIONS = {
    'checkout_success': [],
    'payment_success': [],
    'booking_cancelled': [],
    'stock_threshold_reached': []
}


def dispatch_notify_checkout_success(event):
    for func in NOTIFICATIONS['checkout_success']:
        func(event)


def dispatch_notify_payment_success(event):
    for func in NOTIFICATIONS['payment_success']:
        func(event)


def dispatch_notify_booking_cancelled(event):
    for func in NOTIFICATIONS['booking_cancelled']:
        func(event)


def dispatch_notify_stock_threshold_reached(event):
    for func in NOTIFICATIONS['stock_threshold_reached']:
        func(event)


class MailNotify(object):
    """Mail notifyer.
    """

    def __init__(self, context):
        self.context = context
        self.settings = INotificationSettings(self.context)

    def send(self, subject, message, receiver):
        shop_manager_address = self.settings.admin_email
        if not shop_manager_address:
            raise ValueError('Shop manager address is missing in settings.')
        shop_manager_name = self.settings.admin_name
        if shop_manager_name:
            from_name = safe_encode(shop_manager_name)
            mailfrom = formataddr((from_name, shop_manager_address))
        else:
            mailfrom = shop_manager_address

        api.portal.send_email(
            recipient=receiver,
            sender=mailfrom,
            subject=subject,
            body=message,
        )


def _indent(text, ind=5, width=80):
    """helper indents text"""
    wrapped = textwrap.fill(
        safe_unicode(text),
        width,
        initial_indent=ind * u' '
    )
    return safe_encode(wrapped)


def create_mail_listing(context, order_data):
    """Create item listing for notification mail.
    """
    lines = []
    for booking in order_data.bookings:
        brain = get_catalog_brain(context, booking.attrs['buyable_uid'])
        # fetch buyable
        buyable = brain.getObject()
        # fetch buyable title
        title = safe_encode(booking.attrs['title'])
        # fetch buyable comment
        comment = booking.attrs['buyable_comment']
        if comment:
            title = '%s (%s)' % (title, comment)
        # fetch currency
        currency = booking.attrs['currency']
        # fetch net
        net = booking.attrs['net']
        # build price
        price = '%s %0.2f' % (currency, net)
        # XXX: discount
        state = booking.attrs.get('state')
        state_text = ''
        if state == ifaces.STATE_RESERVED:
            state_text = ' ({})'.format(vocabs.state_vocab()[state])
        line = '{count: 4f} {title}{state} {price}'.format(
            count=booking.attrs['buyable_count'],
            title=title,
            state=state_text,
            price=price,
        )
        lines.append(line)
        if comment:
            lines.append(_indent('({0})'.format(comment)))
        notificationtext = IItemNotificationText(buyable)
        if state == ifaces.STATE_RESERVED:
            text = notificationtext.overbook_text
        elif state == ifaces.STATE_NEW:
            text = notificationtext.order_text
        else:
            text = None
        if text:
            lines.append(_indent(text))
    return '\n'.join([safe_encode(l) for l in lines])


def create_order_summary(context, order_data):
    """Create summary for notification mail.
    """
    attrs = order_data.order.attrs
    cart_total = order_data.total
    # no costs at all
    if not cart_total:
        return ''
    lines = []
    request = getRequest()
    # currency
    currency = order_data.currency
    # cart net and vat
    cart_net = order_data.net
    if cart_net:
        # cart net
        order_summary_cart_net = _(
            'order_summary_cart_net',
            default=u'Net: ${value} ${currency}',
            mapping={
                'value': ascur(cart_net),
                'currency': currency,
            })
        lines.append(translate(order_summary_cart_net, context=request))
        # cart vat
        cart_vat = order_data.vat
        order_summary_cart_vat = _(
            'order_summary_cart_vat',
            default=u'VAT: ${value} ${currency}',
            mapping={
                'value': ascur(cart_vat),
                'currency': currency,
            })
        lines.append(translate(order_summary_cart_vat, context=request))
    # cart discount
    discount_net = order_data.discount_net
    if discount_net:
        # discount net
        order_summary_discount_net = _(
            'order_summary_discount_net',
            default=u'Discount Net: ${value} ${currency}',
            mapping={
                'value': ascur(discount_net),
                'currency': currency,
            })
        lines.append(translate(order_summary_discount_net, context=request))
        # discount vat
        discount_vat = order_data.discount_vat
        order_summary_discount_vat = _(
            'order_summary_discount_vat',
            default=u'Discount VAT: ${value} ${currency}',
            mapping={
                'value': ascur(discount_vat),
                'currency': currency,
            })
        lines.append(translate(order_summary_discount_vat, context=request))
        # discount total
        discount_total = discount_net + discount_vat
        order_summary_discount_total = _(
            'order_summary_discount_total',
            default=u'Discount Total: ${value} ${currency}',
            mapping={
                'value': ascur(discount_total),
                'currency': currency,
            })
        lines.append(translate(order_summary_discount_total, context=request))
    # shipping costs
    shipping_net = order_data.shipping_net
    if shipping_net:
        # shiping label
        shipping_label = attrs['shipping_label']
        order_summary_shipping_label = _(
            'order_summary_shipping_label',
            default=u'Shipping: ${label}',
            mapping={
                'label': translate(shipping_label, context=request),
            })
        lines.append(translate(order_summary_shipping_label, context=request))
        # shiping description
        shipping_description = attrs['shipping_description']
        lines.append(translate(shipping_description, context=request))
        # shiping net
        order_summary_shipping_net = _(
            'order_summary_shipping_net',
            default=u'Shipping Net: ${value} ${currency}',
            mapping={
                'value': ascur(shipping_net),
                'currency': currency,
            })
        lines.append(translate(order_summary_shipping_net, context=request))
        # shiping vat
        shipping_vat = order_data.shipping_vat
        order_summary_shipping_vat = _(
            'order_summary_shipping_vat',
            default=u'Shipping VAT: ${value} ${currency}',
            mapping={
                'value': ascur(shipping_vat),
                'currency': currency,
            })
        lines.append(translate(order_summary_shipping_vat, context=request))
        # shiping total
        shipping_total = shipping_net + shipping_vat
        order_summary_shipping_total = _(
            'order_summary_shipping_total',
            default=u'Shipping Total: ${value} ${currency}',
            mapping={
                'value': ascur(shipping_total),
                'currency': currency,
            })
        lines.append(translate(order_summary_shipping_total, context=request))
    # cart total
    order_summary_cart_total = _(
        'order_summary_cart_total',
        default=u'Total: ${value} ${currency}',
        mapping={
            'value': ascur(cart_total),
            'currency': currency,
        })
    lines.append(translate(order_summary_cart_total, context=request))
    summary_title = translate(
        _('order_summary_label', default=u'Summary:'), context=request)
    summary_text = '\n' + '\n'.join([safe_encode(line) for line in lines])
    return '\n' + safe_encode(summary_title) + summary_text + '\n'


def create_global_text(context, order_data):
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
    global_text = '\n\n'.join([safe_encode(line) for line in notifications])
    if global_text.strip():
        return '\n\n' + global_text.strip() + '\n'
    return ''


def create_payment_text(context, order_data):
    payment = order_data.order.attrs['payment_method']
    payment_text = safe_encode(IPaymentText(getSite()).payment_text(payment))
    if payment_text.strip():
        return '\n\n' + payment_text.strip() + '\n'
    return ''


POSSIBLE_TEMPLATE_CALLBACKS = [
    'booking_cancelled_title',
    'global_text',
    'item_listing',
    'order_summary',
    'payment_text',
    'items_stock_threshold_reached_text'
]


def _process_template_cb(name, tpls, args, context, order_data):
    cb_name = '{0:s}_cb'.format(name)
    if cb_name in tpls:
        args[name] = tpls[cb_name](context, order_data)


def create_mail_body(templates, context, order_data):
    """Creates a rendered mail body

    templates
        Dict with a bunch of cbs and the body template itself.

    context
        Some object in Plone which can be used as a context to acquire from

    order_data
        Order-data instance.
    """
    lang = context.restrictedTraverse('@@plone_portal_state').language()
    attrs = order_data.order.attrs
    arguments = dict(attrs.items())
    arguments['portal_url'] = getSite().absolute_url()
    arguments['date'] = attrs['created'].strftime(DT_FORMAT)
    salutation = translate(attrs['personal_data.gender'],
                           domain='bda.plone.checkout',
                           target_language=lang)
    arguments['salutation'] = safe_encode(salutation)

    # todo: next should be a cb
    if attrs['delivery_address.alternative_delivery']:
        delivery_address_template = templates['delivery_address']
        arguments['delivery_address'] = delivery_address_template % arguments
    else:
        arguments['delivery_address'] = ''

    for name in POSSIBLE_TEMPLATE_CALLBACKS:
        _process_template_cb(
            name,
            templates,
            arguments,
            context,
            order_data
        )
    return templates['body'] % arguments


def do_notify(context, order_data, templates, receiver):
    attrs = order_data.order.attrs
    subject = templates['subject'] % attrs['ordernumber']
    message = create_mail_body(templates, context, order_data)
    mail_notify = MailNotify(context)
    try:
        mail_notify.send(subject, message, receiver)
    except Exception:
        msg = translate(
            _('email_sending_failed',
              default=u'Failed to send notification to ${receiver}',
              mapping={'receiver': receiver}))
        api.portal.show_message(message=msg, request=context.REQUEST)
        logger.exception("Email could not be sent.")


def do_notify_customer(context, order_data, templates):
    customer_address = order_data.order.attrs['personal_data.email']
    do_notify(context, order_data, templates, customer_address)


def do_notify_shopmanager(context, order_data, templates):
    shop_manager_address = INotificationSettings(context).admin_email
    do_notify(context, order_data, templates, shop_manager_address)


def get_order_uid(event):
    if ICheckoutEvent.providedBy(event):
        return event.uid
    if IPaymentEvent.providedBy(event):
        return event.order_uid
    if IBookingCancelledEvent.providedBy(event):
        return event.order_uid
    if IStockThresholdReached.providedBy(event):
        return event.order_uid


def notify_order_success(event, who=None):
    """Send notification mail after order succeed.
    """
    if who not in ['customer', 'shopmanager']:
        raise ValueError(
            'kw "who" mus be one out of ("customer", "shopmanager")'
        )
    order_data = OrderData(event.context, uid=get_order_uid(event))
    templates = dict()
    state = order_data.state
    if state == ifaces.STATE_RESERVED:
        templates.update(get_reservation_templates(event.context))
    elif state == ifaces.STATE_MIXED:
        # XXX: mixed templates
        templates.update(get_reservation_templates(event.context))
    else:
        templates.update(get_order_templates(event.context))
    templates['item_listing_cb'] = create_mail_listing
    templates['order_summary_cb'] = create_order_summary
    templates['global_text_cb'] = create_global_text
    templates['payment_text_cb'] = create_payment_text
    if who == "customer":
        do_notify_customer(event.context, order_data, templates)
    else:
        do_notify_shopmanager(event.context, order_data, templates)


class BookingCancelledTitleCB(object):

    def __init__(self, event):
        self.event = event

    def __call__(self, *args):
        return self.event.booking_attrs['eventtitle']

def notify_booking_cancelled(event, who=None):
    """Send notification mail after booking was cancelled.
    """
    order_data = OrderData(event.context, uid=get_order_uid(event))
    templates = dict()
    templates.update(get_booking_cancelled_templates(event.context))
    templates['booking_cancelled_title_cb'] = BookingCancelledTitleCB(event)
    if who == "customer":
        do_notify_customer(event.context, order_data, templates)
    elif who == 'shopmanager':
        do_notify_shopmanager(event.context, order_data, templates)
    else:
        raise ValueError(
            'kw "who" mus be one out of ("customer", "shopmanager")'
        )

class StockThresholdReachedCB(object):

    def __init__(self, event):
        self.event = event

    def __call__(self, *args):
        items_stock_threshold_reached_text = ""
        items = self.event.items_stock_threshold_reached
        for item_attrs in items:
            title = item_attrs['title']
            remaining_stock = item_attrs['remaining_stock_available']
            items_stock_threshold_reached_text += "%s (Remaining stock: %s)\n" %(title, remaining_stock)

        return items_stock_threshold_reached_text


def notify_stock_threshold_reached(event, who=None):
    """Send notification mail when item is getting out of stock.
    """
    order_data = OrderData(event.context, uid=get_order_uid(event))
    templates = dict()
    templates.update(get_stock_threshold_reached_templates(event.context))
    templates['items_stock_threshold_reached_text_cb'] = StockThresholdReachedCB(event)

    if who == 'shopmanager':
        do_notify_shopmanager(event.context, order_data, templates)
    else:
        raise ValueError(
            'kw "who" mus be one out of ("customer", "shopmanager")'
        )


# below here we have the actual events

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

NOTIFICATIONS['checkout_success'].append(notify_checkout_success_customer)
NOTIFICATIONS['checkout_success'].append(notify_checkout_success_shopmanager)


def notify_payment_success_customer(event):
    """Send notification mail after payment succeed.
    """
    notify_order_success(event, who="customer")


def notify_payment_success_shopmanager(event):
    """Send notification mail after payment succeed.
    """
    notify_order_success(event, who="shopmanager")

NOTIFICATIONS['payment_success'].append(notify_payment_success_customer)
NOTIFICATIONS['payment_success'].append(notify_payment_success_shopmanager)


def notify_booking_cancelled_customer(event):
    notify_booking_cancelled(event, who="customer")


def notify_booking_cancelled_shopmanager(event):
    notify_booking_cancelled(event, who="shopmanager")


NOTIFICATIONS['booking_cancelled'].append(notify_booking_cancelled_customer)
NOTIFICATIONS['booking_cancelled'].append(notify_booking_cancelled_shopmanager)


def notify_stock_threshold_reached_shopmanager(event):
    notify_stock_threshold_reached(event, who="shopmanager")

NOTIFICATIONS['stock_threshold_reached'].append(notify_stock_threshold_reached_shopmanager)


