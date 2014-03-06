from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from bda.plone.cart import get_catalog_brain
from bda.plone.orders import common
from bda.plone.orders import message_factory as _
from bda.plone.orders.common import DT_FORMAT
from bda.plone.orders.common import get_order
from bda.plone.orders.interfaces import INotificationText
from bda.plone.orders.mailtemplates import get_order_templates
from bda.plone.orders.mailtemplates import get_reservation_templates
from email.Header import Header
from email.MIMEText import MIMEText
from email.Utils import formatdate
from repoze.catalog.query import Any
from souper.soup import get_soup
from zope.i18n import translate
import textwrap


def status_message(context, msg):
    putils = getToolByName(context, 'plone_utils')
    putils.addPortalMessage(msg)

def _indent(text, ind=5, width=80):
    text = textwrap(text, width - col)
    lines = []
    for line in text.split('\n'):
        lines.append(' ' * col + line)
    return '\n'.join(lines)

def create_mail_listing(context, attrs):
    """Create item listing for notification mail.
    """
    soup = get_soup('bda_plone_orders_bookings', context)
    bookings = soup.query((Any('uid', attrs['booking_uids'])))
    lines = []
    for booking in bookings:
        brain = get_catalog_brain(context, booking.attrs['buyable_uid'])
        buyable = brain.getObject()
        title = brain.Title
        comment = booking.attrs['buyable_comment']
        if comment:
            title = '%s (%s)' % (title, comment)
        line = '{count: 4f} {title}'.format(
            count=booking.attrs['buyable_count'],
            title=title
        )
        lines.append(line)
        if comment:
            lines.append(_indent('({0})'.format(comment)))
        notificationtext = INotificationText(buyable)
        if attrs['state'] == 'reserved' and notificationtext.overbook_text:
            lines.append(_indent(notificationtext.overbook_text))
        elif attrs['state'] == 'new' and notificationtext.order_text:
            lines.append(_indent(notificationtext.order_text))
    return '\n'.join(lines)


def create_order_total(context, attrs):
    """Calculate order total price for notification mail.

    XXX: use CartItemCalculator? Problem - lives in bda.plone.shop
    XXX: also consider discount here once implemented
    """
    soup = get_soup('bda_plone_orders_bookings', context)
    bookings = soup.query((Any('uid', attrs['booking_uids'])))
    ret = 0.0
    for booking in bookings:
        count = float(booking.attrs['buyable_count'])
        net = booking.attrs.get('net', 0.0) * count
        ret += net
        ret += net * booking.attrs.get('vat', 0.0) / 100
    return "%.2f" % (ret + float(attrs['shipping']))


def create_payment_text(context, attrs):
    pass


def create_mail_body(templates, context, attrs):
    arguments = dict(attrs.items())
    arguments['date'] = attrs['created'].strftime(DT_FORMAT)
    if attrs['delivery_address.alternative_delivery']:
        delivery_address_template = templates['delivery_address']
        arguments['delivery_address'] = delivery_address_template % arguments
    else:
        arguments['delivery_address'] = ''
    item_listing_callback = templates['item_listing_callback']
    arguments['item_listing'] = item_listing_callback(context, attrs)
    order_total_callback = templates['order_total_callback']
    arguments['order_total'] = order_total_callback(context, attrs)
    body_template = templates['body']
    return body_template % arguments


def do_notify(context, order, templates):
    attrs = order.attrs
    subject = templates['subject'] % attrs['ordernumber']
    message = create_mail_body(templates, context, attrs)
    customer_address = attrs['personal_data.email']
    props = getToolByName(context, 'portal_properties')
    shop_manager_address = props.site_properties.email_from_address
    mail_notify = MailNotify(context)
    for receiver in [customer_address, shop_manager_address]:
        try:
            mail_notify.send(subject, message, receiver)
        except Exception:
            msg = translate(
                _('email_sending_failed',
                  default=u'Failed to send Notification to ${receiver}',
                  mapping={'receiver': receiver}))
            status_message(context, msg)


def notify_payment_success(event):
    """Send notification mail after payment succeed.
    """
    order = get_order(event.context, event.order_uid)
    templates = dict()
    templates.update(get_order_templates(event.context))
    templates['item_listing_callback'] = create_mail_listing
    templates['order_total_callback'] = create_order_total
    templates['payment_text_callback'] = create_payment_text
    do_notify(event.context, order, templates)


def notify_reservation_if_payment_skipped(event):
    """Send notification mail after checkout done if reservation and payment
    skipped.
    """
    if not common.SKIP_PAYMENT_IF_RESERVED:
        return
    order = get_order(event.context, event.uid)
    if order.attrs['state'] != 'reserved':
        return
    templates = dict()
    templates.update(get_reservation_templates(event.context))
    templates['item_listing_callback'] = create_mail_listing
    templates['order_total_callback'] = create_order_total
    templates['payment_text_callback'] = create_payment_text
    do_notify(event.context, order, templates)


class MailNotify(object):
    """Mail notifyer.
    """

    def __init__(self, context):
        self.context = context

    def send(self, subject, message, receiver):
        purl = getToolByName(self.context, 'portal_url')
        mailfrom = purl.getPortalObject().email_from_address
        mailfrom_name = purl.getPortalObject().email_from_name
        if mailfrom_name:
            mailfrom = u"%s <%s>" % (safe_unicode(mailfrom_name), mailfrom)
        mailhost = getToolByName(self.context, 'MailHost')
        subject = subject.encode('utf-8')
        subject = Header(subject, 'utf-8')
        message = MIMEText(message, _subtype='plain')
        message.set_charset('utf-8')
        message.add_header('Date',  formatdate(localtime=True))
        message.add_header('From_', mailfrom)
        message.add_header('From', mailfrom)
        message.add_header('To', receiver)
        message['Subject'] = subject
        mailhost.send(messageText=message,
                      mto=receiver)
