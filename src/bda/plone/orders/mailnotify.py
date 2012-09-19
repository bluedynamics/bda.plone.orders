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
from .mailtemplates import get_templates


_ = MessageFactory('bda.plone.orders')


def message(context, msg):
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
        line = '    %s: %s' % (title, booking.attrs['buyable_count'])
        lines.append(line)
    return '\n'.join(lines)


def create_mail_body(context, attrs):
    templates = get_templates(context)
    arguments = dict()
    arguments['date'] = attrs['created'].strftime(DT_FORMAT)
    arguments['personal_data.name'] = attrs['personal_data.name']
    arguments['personal_data.surname'] = attrs['personal_data.surname']
    arguments['personal_data.company'] = attrs['personal_data.company']
    arguments['personal_data.phone'] = attrs['personal_data.phone']
    arguments['billing_address.street'] = attrs['billing_address.street']
    arguments['billing_address.zip'] = attrs['billing_address.zip']
    arguments['billing_address.city'] = attrs['billing_address.city']
    arguments['billing_address.country'] = attrs['billing_address.country']
    if attrs['delivery_address.alternative_delivery']:
        delivery = dict()
        delivery['delivery_address.name'] = attrs['delivery_address.name']
        delivery['delivery_address.surname'] = attrs['delivery_address.surname']
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
    arguments['item_listing'] = create_mail_listing(context, attrs)
    body_template = templates['body']
    return body_template % arguments


def notify_order(event):
    """Send notification mail after checkout succeed.
    """
    context = event.context
    order = get_order(context, event.order_uid)
    attrs = order.attrs
    templates = get_templates(context)
    subject = templates['subject']
    message = create_mail_body(context, attrs)
    customer_address = attrs['personal_data.email']
    props = getToolByName(context, 'portal_properties')
    shop_manager_address = props.site_properties.email_from_address
    mail_notify = MailNotify(context)
    for receiver in [customer_address, shop_manager_address]:
        try:
            mail_notify.send(subject, message, receiver)
        except Exception, e:
            msg = translate(
                _('email_sending_failed',
                  'Failed to send Notification to ${receiver}',
                  mapping={'receiver': receiver}))
            message(context, msg)


class MailNotify(object):
    """Mail notifyer.
    """
    
    def __init__(self, context):
        self.context = context
    
    def send(self, subject, message, receiver):
        sent_key = '_order_mail_already_sent_%s' % receiver
        if self.context.REQUEST.get(sent_key):
            return
        purl = getToolByName(self.context, 'portal_url')
        mailfrom = purl.getPortalObject().email_from_address
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
        server = mailhost.smtp_host
        port = mailhost.smtp_port
        user = mailhost.smtp_uid
        passwd = mailhost.smtp_pwd
        server = smtplib.SMTP(server, port)
        server.login(user, passwd)
        server.set_debuglevel(0)
        from_ = message['From_']
        message = message.as_string()
        server.sendmail(from_, receiver, message)
        server.quit()
        self.context.REQUEST[sent_key] = 1
