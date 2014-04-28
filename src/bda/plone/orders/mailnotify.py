from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from bda.plone.cart import get_catalog_brain
from bda.plone.orders import common
from bda.plone.orders import interfaces as ifaces
from bda.plone.orders import message_factory as _
from bda.plone.orders import safe_encode
from bda.plone.orders.common import DT_FORMAT
from bda.plone.orders.common import OrderData
from bda.plone.orders.interfaces import IGlobalNotificationText
from bda.plone.orders.interfaces import IItemNotificationText
from bda.plone.orders.interfaces import INotificationSettings
from bda.plone.orders.interfaces import IPaymentText
from bda.plone.orders.mailtemplates import get_order_templates
from bda.plone.orders.mailtemplates import get_reservation_templates
from email.Header import Header
from email.MIMEText import MIMEText
from email.Utils import formatdate
from zope.component.hooks import getSite
from zope.i18n import translate

import logging
import textwrap


logger = logging.getLogger('bda.plone.orders')


def status_message(context, msg):
    putils = getToolByName(context, 'plone_utils')
    putils.addPortalMessage(msg)


def _indent(text, ind=5, width=80):
    text = textwrap.wrap(text, width - ind)
    lines = []
    for line in text:
        lines.append(u' ' * ind + safe_unicode(line))
    return safe_encode(u'\n'.join(lines))


def create_mail_listing(context, order_data):
    """Create item listing for notification mail.
    """
    lines = []
    for booking in order_data.bookings:
        brain = get_catalog_brain(context, booking.attrs['buyable_uid'])
        buyable = brain.getObject()
        title = safe_encode(booking.attrs['title'])
        comment = booking.attrs['buyable_comment']
        if comment:
            title = '%s (%s)' % (title, comment)
        # XXX: price and discount
        line = '{count: 4f} {title}'.format(
            count=booking.attrs['buyable_count'],
            title=title
        )
        lines.append(line)
        if comment:
            lines.append(_indent('({0})'.format(comment)))
        notificationtext = IItemNotificationText(buyable)
        if booking.attrs['state'] == ifaces.STATE_RESERVED:
            text = notificationtext.overbook_text
            if text:
                lines.append(_indent(safe_encode(text)))
        elif booking.attrs['state'] == ifaces.STATE_NEW:
            text = notificationtext.order_text
            if text:
                lines.append(_indent(safe_encode(text)))
    return '\n'.join(lines)


def create_order_total(context, order_data):
    """
    """
    # XXX: refactor to order summary
    #ret = 0.0
    #for booking in order_data.bookings:
    #    count = float(booking.attrs['buyable_count'])
    #    net = booking.attrs.get('net', 0.0) * count
    #    ret += net
    #    ret += net * booking.attrs.get('vat', 0.0) / 100
    #return "%.2f" % (ret + float(attrs['shipping']))
    return "%.2f" % 999.0


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
                notifications.add(safe_encode(text))
        elif order_state == ifaces.STATE_NEW:
            text = notificationtext.global_order_text
            if text:
                notifications.add(safe_encode(text))
    return '\n\n'.join(notifications)


def create_payment_text(context, order_data):
    payment = order_data.order.attrs['payment_method']
    return safe_encode(IPaymentText(getSite()).payment_text(payment))


def create_mail_body(templates, context, order_data):
    """Creates a rendered mail body

    templates
        Dict with a bunch of callbacks and the body template itself.

    context
        Some object in Plone which can be used as a context to acquire from

    order_data
        Order-data instance.
    """
    attrs = order_data.order.attrs
    arguments = dict(attrs.items())
    arguments['portal_url'] = getSite().absolute_url()
    arguments['date'] = attrs['created'].strftime(DT_FORMAT)
    if attrs['delivery_address.alternative_delivery']:
        delivery_address_template = templates['delivery_address']
        arguments['delivery_address'] = delivery_address_template % arguments
    else:
        arguments['delivery_address'] = ''
    item_listing_callback = templates['item_listing_callback']
    arguments['item_listing'] = item_listing_callback(context, order_data)
    order_total_callback = templates['order_total_callback']
    arguments['order_total'] = order_total_callback(context, order_data)
    global_text_callback = templates['global_text_callback']
    arguments['global_text'] = global_text_callback(context, order_data)
    payment_text_callback = templates['payment_text_callback']
    arguments['payment_text'] = payment_text_callback(context, order_data)
    body_template = templates['body']
    return body_template % arguments


def do_notify(context, order_data, templates):
    attrs = order_data.order.attrs
    subject = templates['subject'] % attrs['ordernumber']
    message = create_mail_body(templates, context, order_data)
    customer_address = attrs['personal_data.email']
    shop_manager_address = INotificationSettings(context).admin_email
    mail_notify = MailNotify(context)
    for receiver in [customer_address, shop_manager_address]:
        try:
            mail_notify.send(subject, message, receiver)
        except Exception, e:
            msg = translate(
                _('email_sending_failed',
                  default=u'Failed to send Notification to ${receiver}',
                  mapping={'receiver': receiver}))
            status_message(context, msg)
            logger.error("Email could not be sent: %s" % str(e))


def notify_payment_success(event):
    """Send notification mail after payment succeed.
    """
    templates = dict()
    templates.update(get_order_templates(event.context))
    templates['item_listing_callback'] = create_mail_listing
    templates['order_total_callback'] = create_order_total
    templates['global_text_callback'] = create_global_text
    templates['payment_text_callback'] = create_payment_text
    order_data = OrderData(event.context, uid=event.order_uid)
    do_notify(event.context, order_data, templates)


def notify_reservation_if_payment_skipped(event):
    """Send notification mail after checkout done if reservation and payment
    skipped.
    """
    if not common.SKIP_PAYMENT_IF_RESERVED:
        return
    order_data = OrderData(event.context, uid=event.uid)
    # TODO: state mixed might be handled separately
    if order_data.state not in (ifaces.STATE_RESERVED, ifaces.STATE_MIXED):
        return
    templates = dict()
    templates.update(get_reservation_templates(event.context))
    templates['item_listing_callback'] = create_mail_listing
    templates['order_total_callback'] = create_order_total
    templates['global_text_callback'] = create_global_text
    templates['payment_text_callback'] = create_payment_text
    do_notify(event.context, order_data, templates)


class MailNotify(object):
    """Mail notifyer.
    """

    def __init__(self, context):
        self.context = context

    def send(self, subject, message, receiver):
        settings = INotificationSettings(self.context)
        shop_manager_address = settings.admin_email
        shop_manager_name = settings.admin_name
        if shop_manager_name:
            mailfrom = u"%s <%s>" % (
                safe_unicode(shop_manager_name), shop_manager_address)
        mailhost = getToolByName(self.context, 'MailHost')
        message = MIMEText(message, _subtype='plain')
        message.set_charset('utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        message['From_'] = Header(mailfrom, 'utf-8')
        message['From'] = Header(mailfrom, 'utf-8')
        message['To'] = Header(receiver, 'utf-8')
        message.add_header('Date', formatdate(localtime=True))
        mailhost.send(messageText=message, mto=receiver)
