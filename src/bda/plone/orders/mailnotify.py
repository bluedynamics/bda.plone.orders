import smtplib
from email.MIMEText import MIMEText
from email.Utils import formatdate
from email.Header import Header
from zope.i18n import translate
from zope.i18nmessageid import MessageFactory
from souper.soup import get_soup
from repoze.catalog.query import Any
from Products.CMFCore.utils import getToolByName
from bda.plone.cart import get_catalog_brain
from .common import (
    DT_FORMAT,
    get_order,
)
from .mailtemplates import (
    get_order_templates,
    get_reservation_templates,
)
from Products.CMFPlone.utils import safe_unicode
from . import common


_ = MessageFactory('bda.plone.orders')


def status_message(context, msg):
    putils = getToolByName(context, 'plone_utils')
    putils.addPortalMessage(msg)


def create_mail_listing(context, attrs):
    soup = get_soup('bda_plone_orders_bookings', context)
    bookings = soup.query((Any('uid', attrs['booking_uids'])))
    lines = []
    for booking in bookings:
        buyable = get_catalog_brain(context, booking.attrs['buyable_uid'])
        title = buyable.Title
        comment = booking.attrs['buyable_comment']
        if comment:
            title = '%s (%s)' % (title, comment)
        line = '    %s %s' % (booking.attrs['buyable_count'], title)
        lines.append(line)
    return '\n'.join(lines)


def create_order_total(context, attrs):
    soup = get_soup('bda_plone_orders_bookings', context)
    bookings = soup.query((Any('uid', attrs['booking_uids'])))
    ret = 0.0
    for booking in bookings:
        count = float(booking.attrs['buyable_count'])
        net = booking.attrs.get('net', 0.0) * count
        ret += net
        ret += net * booking.attrs.get('vat', 0.0) / 100
    return  "%.2f" %(ret + float(attrs['shipping']))


def create_mail_body(templates, context, attrs):
    arguments = dict()
    arguments['date'] = attrs['created'].strftime(DT_FORMAT)
    arguments['ordernumber'] = attrs['ordernumber']
    arguments['personal_data.firstname'] = attrs['personal_data.firstname']
    arguments['personal_data.lastname'] = attrs['personal_data.lastname']
    arguments['personal_data.company'] = attrs['personal_data.company']
    arguments['personal_data.phone'] = attrs['personal_data.phone']
    arguments['personal_data.email'] = attrs['personal_data.email']
    arguments['billing_address.street'] = attrs['billing_address.street']
    arguments['billing_address.zip'] = attrs['billing_address.zip']
    arguments['billing_address.city'] = attrs['billing_address.city']
    arguments['billing_address.country'] = attrs['billing_address.country']
    if attrs['delivery_address.alternative_delivery']:
        delivery = dict()
        delivery['delivery_address.firstname'] = attrs['delivery_address.firstname']
        delivery['delivery_address.lastname'] = attrs['delivery_address.lastname']
        delivery['delivery_address.company'] = attrs['delivery_address.company']
        delivery['delivery_address.street'] = attrs['delivery_address.street']
        delivery['delivery_address.zip'] = attrs['delivery_address.zip']
        delivery['delivery_address.city'] = attrs['delivery_address.city']
        delivery['delivery_address.country'] = attrs['delivery_address.country']
        delivery_address_template = templates['delivery_address']
        arguments['delivery_address'] = delivery_address_template % delivery
    else:
        arguments['delivery_address'] = ''
    arguments['order_comment.comment'] = attrs['order_comment.comment']
    item_listing_callback = templates['item_listing_callback']
    arguments['item_listing'] = item_listing_callback(context, attrs)
    order_total_callback = templates['order_total_callback']
    arguments['order_total'] = order_total_callback(context, attrs)
    body_template = templates['body']
    return body_template % arguments


def do_notify(context, name, order, templates):
    attrs = order.attrs
    subject = templates['subject'] % attrs['ordernumber']
    message = create_mail_body(templates, context, attrs)
    customer_address = attrs['personal_data.email']
    props = getToolByName(context, 'portal_properties')
    shop_manager_address = props.site_properties.email_from_address
    mail_notify = MailNotify(context, name)
    for receiver in [customer_address, shop_manager_address]:
        try:
            mail_notify.send(subject, message, receiver)
        except Exception, e:
            msg = translate(
                _('email_sending_failed',
                  'Failed to send Notification to ${receiver}',
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
    do_notify(event.context, 'order', order, templates)


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
    do_notify(event.context, 'reservation', order, templates)


class MailNotify(object):
    """Mail notifyer.
    """

    def __init__(self, context, name):
        self.context = context
        self.name = name

    def send(self, subject, message, receiver):
        sent_key = '_%s_mail_already_sent_%s' % (self.name, receiver)
        if self.context.REQUEST.get(sent_key):
            return
        purl = getToolByName(self.context, 'portal_url')
        mailfrom = purl.getPortalObject().email_from_address
        # disable mailfrom name because of wrong encoding
        # mailfrom_name = purl.getPortalObject().email_from_name
        # if mailfrom_name:
        #     mailfrom = u"%s <%s>" % (safe_unicode(mailfrom_name), mailfrom)
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
        self.context.REQUEST[sent_key] = 1
