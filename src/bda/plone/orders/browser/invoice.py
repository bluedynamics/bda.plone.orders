# -*- coding: utf-8 -*-
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bda.plone.cart import ascur
from bda.plone.orders import message_factory as _
from bda.plone.orders.browser.common import ContentViewBase
from bda.plone.orders.browser.common import ContentTemplateView
from bda.plone.orders.browser.order import OrderDataView
from bda.plone.orders.browser.order import ProtectedOrderDataView
from bda.plone.orders.common import DT_FORMAT_SHORT
from bda.plone.orders.interfaces import IInvoiceSender


###############################################################################
# invoice
###############################################################################

class InvoiceViewBase(OrderDataView):
    invoice_prefix = u'INV'

    @property
    def sender(self):
        # XXX: right now we provide a global sender for invoices. in order to
        #      provide vendors there's more to do. there need to be an option
        #      whether the invoice gets splitted to specific vendors and if so
        #      multiple invoices need to be available for one order. this also
        #      needs to be reflected in order emails. if there is one billing
        #      point even if there are multiple vendors for one order the
        #      global sender address is used (which is actually the current
        #      and only behavior).
        sender = IInvoiceSender(self.context)
        return {
            'company': sender.company,
            'companyadd': sender.companyadd,
            'firstname': sender.firstname,
            'lastname': sender.lastname,
            'street': sender.street,
            'zip': sender.zip,
            'city': sender.city,
            'country': sender.country,
            'phone': sender.phone,
            'email': sender.email,
            'web': sender.web,
            'iban': sender.iban,
            'bic': sender.bic
        }

    @property
    def invoice_number(self):
        return '{}{}'.format(self.invoice_prefix, self.order['ordernumber'])

    @property
    def created(self):
        value = self.order.get('created', _('unknown', default=u'Unknown'))
        if value:
            value = value.strftime(DT_FORMAT_SHORT)
        return value

    @property
    def listing(self):
        ret = list()
        for booking in self.order_data.bookings:
            data = dict()
            data['title'] = safe_unicode(booking.attrs['title'])
            data['item_number'] = safe_unicode(booking.attrs['item_number'])
            data['comment'] = safe_unicode(booking.attrs['buyable_comment'])
            data['currency'] = safe_unicode(booking.attrs['currency'])
            data['count'] = booking.attrs['buyable_count']
            data['net'] = booking.attrs.get('net', 0.0)
            data['vat'] = booking.attrs.get('vat', 0.0)
            data['discount_net'] = float(booking.attrs['discount_net'])
            data['quantity_unit'] = booking.attrs.get('quantity_unit')
            ret.append(data)
        return ret

    def summary(self):
        order_data = self.order_data
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
        shipping_net = order_data.shipping_net
        data['shipping_net'] = shipping_net
        shipping_vat = order_data.shipping_vat
        data['shipping_vat'] = shipping_vat
        shipping_total = shipping_net + shipping_vat
        data['shipping_total'] = shipping_total
        cart_total = order_data.total
        data['cart_total'] = cart_total
        return data

    def ascur(self, val):
        return ascur(val)


class InvoiceView(InvoiceViewBase, ContentViewBase, ContentTemplateView):
    """Invoice view.
    """
    content_template = ViewPageTemplateFile('templates/invoice.pt')


class DirectInvoiceView(InvoiceViewBase, ProtectedOrderDataView):
    """Direct Invoice view.
    """
    content_template = ViewPageTemplateFile('templates/invoice.pt')
