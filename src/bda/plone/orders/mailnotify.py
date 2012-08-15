import smtplib
from email.MIMEText import MIMEText
from email.Utils import formatdate
from email.Header import Header
from souper.soup import get_soup
from repoze.catalog.query import Any
from Products.CMFCore.utils import getToolByName
from bda.plone.cart import get_catalog_brain
from .common import DT_FORMAT


MAIL_SUBJECT = u'Order received.'

MAIL_BODY = """
Date: %(date)s

Personal Data:
Name: %(personal_data.name)s %(personal_data.surname)s
Company: %(personal_data.company)s
Phone: %(personal_data.phone)s

Address:
Street: %(billing_address.street)s
ZIP: %(billing_address.zip)s
City: %(billing_address.city)s
Country: %(billing_address.country)s
%(delivery_address)s
Comment:
%(order_comment.comment)s

Ordered items:
%(item_listing)s
"""

DELIVERY_ADDRESS = """
Delivery Address:
Name: %(delivery_address.name)s %(delivery_address.surname)s
Company: %(delivery_address.company)s
Street: %(delivery_address.street)s
ZIP: %(delivery_address.zip)s
City: %(delivery_address.city)s
Country: %(delivery_address.country)s
"""


def create_mail_listing(context, attrs):
    soup = get_soup('bda_plone_orders_bookings', context)
    bookings = soup.query((Any('buyable_uid', attrs['booking_uids'])))
    lines = []
    for booking in bookings:
        buyable = get_catalog_brain(context, booking.attrs['buyable_uid'])
        line = '    %s: %s' % (buyable.Title, booking.attrs['buyable_count'])
        lines.append(line)
    return '\n'.join(lines)


def create_mail_body(context, attrs):
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
        arguments['delivery_address'] = DELIVERY_ADDRESS % delivery
    else:
        arguments['delivery_address'] = ''
    arguments['order_comment.comment'] = attrs['order_comment.comment']
    arguments['item_listing'] = create_mail_listing(context, attrs)
    return MAIL_BODY % arguments


def checkout_success(event):
    """Send notification mail after checkout succeed.
    """
    subject = MAIL_SUBJECT
    message = create_mail_body(event.context, event.vessel)
    receiver = event.vessel['personal_data.email']
    notify = MailNotify(event.context)
    notify.send(subject, message, receiver)


class MailNotify(object):
    """Mail notifyer.
    """
    
    def __init__(self, context):
        self.context = context
    
    def send(self, subject, message, receiver):
        if self.context.REQUEST.get('_order_mail_already_sent') == 1:
            return True
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
        self.context.REQUEST['_order_mail_already_sent'] = 1