from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from StringIO import StringIO
from bda.plone.cart import ascur
from bda.plone.orders.common import DT_FORMAT
from bda.plone.orders.common import OrderData
from bda.plone.orders.common import OrderTransitions
from bda.plone.orders.common import get_order
from bda.plone.payment import Payments
from decimal import Decimal
from repoze.catalog.query import Contains
from repoze.catalog.query import Eq
from repoze.catalog.query import Ge
from repoze.catalog.query import Le
from souper.soup import LazyRecord
from souper.soup import get_soup
from yafowil.base import ExtractionError
from yafowil.controller import Controller
from yafowil.plone.form import YAMLForm
from yafowil.utils import Tag
from zope.i18n import translate
from zope.i18nmessageid import Message
from zope.i18nmessageid import MessageFactory

import csv
import datetime
import json


_ = MessageFactory('bda.plone.orders')
_co = MessageFactory('bda.plone.checkout')


class Translate(object):

    def __init__(self, request):
        self.request = request

    def __call__(self, msg):
        if not isinstance(msg, Message):
            return msg
        return translate(msg, context=self.request)


class Dropdown(object):
    render = ViewPageTemplateFile('dropdown.pt')
    name = ''
    css = 'dropdown'
    action = ''
    vocab = {}
    transitions = {}
    value = ''

    def __init__(self, context, request, record):
        self.context = context
        self.request = request
        self.record = record

    def create_items(self, transitions):
        uid = str(self.record.attrs['uid'])
        url = self.context.absolute_url()
        ret = list()
        for transition in transitions:
            ret.append({
                'title': self.transitions[transition],
                'target': '%s?transition=%s&uid=%s' % (url, transition, uid)
            })
        return ret

    @property
    def identifyer(self):
        return '%s-%s' % (self.name, str(self.record.attrs['uid']))

    @property
    def ajax_action(self):
        return '%s:#%s-%s:replace' % (self.action,
                                      self.name,
                                      str(self.record.attrs['uid']))

    @property
    def items(self):
        raise NotImplementedError(u"Abstract Dropdown does not implement "
                                  u"``items``.")


state_vocab = {
    'new': _('new', 'New'),
    'finished': _('finished', 'Finished'),
    'cancelled': _('cancelled', 'Cancelled'),
    'reserved': _('reserved', 'Reserved'),
}


class StateDropdown(Dropdown):
    name = 'state'
    css = 'dropdown change_order_state_dropdown'
    action = 'statetransition'
    vocab = state_vocab
    transitions = {
        'renew': _('renew', 'Renew'),
        'finish': _('finish', 'Finish'),
        'cancel': _('cancel', 'Cancel'),
    }

    @property
    def value(self):
        return self.record.attrs['state']

    @property
    def items(self):
        state = self.record.attrs['state']
        transitions = list()
        if state in ['new', 'reserved']:
            transitions = ['finish', 'cancel']
        else:
            transitions = ['renew']
        return self.create_items(transitions)


salaried_vocab = {
    'yes': _('yes', 'Yes'),
    'no': _('no', 'No'),
    'failed': _('failed', 'Failed'),
}


class SalariedDropdown(Dropdown):
    name = 'salaried'
    css = 'dropdown change_order_salaried_dropdown'
    action = 'salariedtransition'
    vocab = salaried_vocab
    transitions = {
        'mark_salaried': _('mark_salaried', 'Mark salaried'),
        'mark_outstanding': _('mark_outstanding', 'Mark outstanding'),
    }

    @property
    def value(self):
        return self.record.attrs.get('salaried', 'no')

    @property
    def items(self):
        salaried = self.record.attrs.get('salaried', 'no')
        transitions = list()
        if salaried == 'yes':
            transitions = ['mark_outstanding']
        else:
            transitions = ['mark_salaried']
        return self.create_items(transitions)


class Transition(BrowserView):
    dropdown = None

    def __call__(self):
        transition = self.request['transition']
        uid = self.request['uid']
        record = OrderTransitions(self.context).do_transition(uid, transition)
        return self.dropdown(self.context, self.request, record).render()


class StateTransition(Transition):
    dropdown = StateDropdown


class SalariedTransition(Transition):
    dropdown = SalariedDropdown


class TableData(BrowserView):
    soup_name = None
    search_text_index = None

    @property
    def columns(self):
        """Return list of dicts with column definitions:

        [{
            'id': 'colid',
            'label': 'Col Label',
            'renderer': callback,
        }]
        """
        raise NotImplementedError(u"Abstract DataTable does not implement "
                                  u"``columns``.")

    def query(self, soup):
        """Return 2-tuple with result length and lazy record iterator.
        """
        raise NotImplementedError(u"Abstract DataTable does not implement "
                                  u"``query``.")

    def sort(self):
        columns = self.columns
        sortparams = dict()
        sortcols_idx = int(self.request.form.get('iSortCol_0'))
        sortparams['index'] = columns[sortcols_idx]['id']
        sortparams['reverse'] = self.request.form.get('sSortDir_0') == 'desc'
        return sortparams

    def all(self, soup):
        data = soup.storage.data
        sort = self.sort()
        sort_index = soup.catalog[sort['index']]
        iids = sort_index.sort(data.keys(), reverse=sort['reverse'])

        def lazyrecords():
            for iid in iids:
                yield LazyRecord(iid, soup)
        return soup.storage.length.value, lazyrecords()

    def slice(self, fullresult):
        start = int(self.request.form['iDisplayStart'])
        length = int(self.request.form['iDisplayLength'])
        count = 0
        for lr in fullresult:
            if count >= start and count < (start + length):
                yield lr
            if count >= (start + length):
                break
            count += 1

    def column_def(self, colname):
        for column in self.columns:
            if column['id'] == colname:
                return column

    def __call__(self):
        soup = get_soup(self.soup_name, self.context)
        aaData = list()
        length, lazydata = self.query(soup)
        columns = self.columns
        colnames = [_['id'] for _ in columns]

        def record2list(record):
            result = list()
            for colname in colnames:
                coldef = self.column_def(colname)
                renderer = coldef.get('renderer')
                if renderer:
                    value = renderer(colname, record)
                else:
                    value = record.attrs.get(colname, '')
                result.append(value)
            return result
        for lazyrecord in self.slice(lazydata):
            aaData.append(record2list(lazyrecord()))
        data = {
            "sEcho": int(self.request.form['sEcho']),
            "iTotalRecords": soup.storage.length.value,
            "iTotalDisplayRecords": length,
            "aaData": aaData,
        }
        return json.dumps(data)


class OrdersTable(BrowserView):
    table_template = ViewPageTemplateFile('table.pt')
    table_id = 'bdaploneorders'

    @property
    def rendered_table(self):
        return self.table_template(self)

    @property
    def ajaxurl(self):
        return '%s/%s' % (self.context.absolute_url(), '@@ordersdata')

    @property
    def columns(self):
        return [{
            'id': 'actions',
            'label': _('actions', 'Actions'),
            'renderer': self.render_order_actions,
        }, {
            'id': 'created',
            'label': _('date', 'Date'),
            'renderer': self.render_dt,
        }, {
            'id': 'personal_data.lastname',
            'label': _('lastname', 'Last Name'),
        }, {
            'id': 'personal_data.firstname',
            'label': _('firstname', 'First Name'),
        }, {
            'id': 'billing_address.city',
            'label': _('city', 'City'),
        }, {
            'id': 'salaried',
            'label': _('salaried', 'Salaried'),
            'renderer': self.render_salaried,
        }, {
            'id': 'state',
            'label': _('state', 'State'),
            'renderer': self.render_state,
        }]

    def render_dt(self, colname, record):
        value = record.attrs.get(colname, '')
        if value:
            value = value.strftime(DT_FORMAT)
        return value

    def render_order_actions(self, colname, record):
        tag = Tag(Translate(self.request))
        target = '%s?uid=%s' % (self.context.absolute_url(),
                                str(record.attrs['uid']))
        link_attrs = {
            'ajax:bind': 'click',
            'ajax:target': target,
            'ajax:overlay': 'order',
            'class_': 'contenttype-document',
            'href': '',
            'title': _('view_order', 'View Order'),
        }
        return tag('a', '&nbsp', **link_attrs)

    def render_salaried(self, colname, record):
        return SalariedDropdown(self.context, self.request, record).render()

    def render_state(self, colname, record):
        return StateDropdown(self.context, self.request, record).render()


class OrdersData(OrdersTable, TableData):
    soup_name = 'bda_plone_orders_orders'
    search_text_index = 'text'

    def query(self, soup):
        sort = self.sort()
        term = self.request.form['sSearch'].decode('utf-8')
        if term:
            res = soup.lazy(Contains(self.search_text_index, term),
                            sort_index=sort['index'],
                            reverse=sort['reverse'],
                            with_size=True)
            length = res.next()
            return length, res
        return self.all(soup)


class OrderView(BrowserView):

    @property
    def uid(self):
        return self.request.form['uid']

    @property
    def order(self):
        return dict(self.order_data.order.attrs)

    @property
    def order_data(self):
        return OrderData(self.context, uid=self.uid)

    @property
    def net(self):
        return ascur(self.order_data.net)

    @property
    def vat(self):
        return ascur(self.order_data.vat)

    @property
    def shipping(self):
        return ascur(self.order_data.shipping)

    @property
    def total(self):
        return ascur(self.order_data.total)

    @property
    def currency(self):
        currency = None
        for booking in self.order_data.bookings:
            if currency is None:
                currency = booking.attrs.get('currency')
            if currency != booking.attrs.get('currency'):
                return None
        return currency

    @property
    def listing(self):
        ret = list()
        for booking in self.order_data.bookings:
            ret.append({
                'title': booking.attrs['title'],
                'count': booking.attrs['buyable_count'],
                'net': ascur(booking.attrs.get('net', 0.0)),
                'vat': booking.attrs.get('vat', 0.0),
                'exported': booking.attrs['exported'],
                'comment': booking.attrs['buyable_comment'],
                'quantity_unit': booking.attrs.get('quantity_unit'),
                'currency': booking.attrs.get('currency'),
            })
        return ret

    def gender(self, order):
        gender = order['personal_data.gender']
        if gender == 'male':
            return _co('male', 'Male')
        if gender == 'female':
            return _co('female', 'Female')
        return gender

    def payment(self, order):
        name = order['payment_selection.payment']
        payment = Payments(self.context).get(name)
        if payment:
            return payment.label
        return name

    def salaried(self, order):
        salaried = order.get('salaried', 'no')
        return salaried_vocab[salaried]

    def tid(self, order):
        tid = order.get('tid', 'none')
        if tid == 'none':
            return _('none', 'None')
        return tid

    def state(self, order):
        return state_vocab[order.get('state', 'new')]

    def created(self, order):
        value = order.get('created', _('unknown', 'Unknown'))
        if value:
            value = value.strftime(DT_FORMAT)
        return value

    def exported(self, item):
        return item['exported'] and _('yes', 'Yes') or _('no', 'No')


class DialectExcelWithColons(csv.excel):
    delimiter = ';'


csv.register_dialect('excel-colon', DialectExcelWithColons)


ORDER_EXPORT_ATTRS = [
    'uid',
    'created',
    'ordernumber',
    'salaried',
    'state',
    'personal_data.company',
    'personal_data.email',
    'personal_data.gender',
    'personal_data.firstname',
    'personal_data.phone',
    'personal_data.lastname',
    'billing_address.city',
    'billing_address.country',
    'billing_address.street',
    'billing_address.zip',
    'delivery_address.alternative_delivery',
    'delivery_address.city',
    'delivery_address.company',
    'delivery_address.country',
    'delivery_address.firstname',
    'delivery_address.street',
    'delivery_address.lastname',
    'delivery_address.zip',
    'order_comment.comment',
    'payment_selection.payment',
]
BOOKING_EXPORT_ATTRS = [
    'title',
    'buyable_comment',
    'buyable_count',
    'quantity_unit',
    'net',
    'vat',
    'currency',
    'exported',
]


class ExportOrdersForm(YAMLForm):
    browser_template = ViewPageTemplateFile('export.pt')
    form_template = 'bda.plone.orders.browser:forms/orders_export.yaml'
    message_factory = _
    action_resource = 'exportorders'

    def __call__(self):
        self.prepare()
        controller = Controller(self.form, self.request)
        if not controller.next:
            self.rendered_form = controller.rendered
            return self.browser_template(self)
        return controller.next

    def from_before_to(self, widget, data):
        from_date = data.fetch('exportorders.from').extracted
        to_date = data.fetch('exportorders.to').extracted
        if to_date <= from_date:
            raise ExtractionError(_('from_date_before_to_date',
                                    'From-date after to-date'))
        return data.extracted

    def export(self, widget, data):
        self.from_date = data.fetch('exportorders.from').extracted
        self.to_date = data.fetch('exportorders.to').extracted

    def export_val(self, record, attr_name):
        val = record.attrs.get(attr_name)
        if isinstance(val, datetime.datetime):
            val = val.strftime(DT_FORMAT)
        if val == '-':
            val = ''
        if isinstance(val, float) or \
           isinstance(val, Decimal):
            val = str(val).replace('.', ',')
        return val

    def csv(self, request):
        orders_soup = get_soup('bda_plone_orders_orders', self.context)
        bookings_soup = get_soup('bda_plone_orders_bookings', self.context)
        query = Ge('created', self.from_date) & Le('created', self.to_date)
        sio = StringIO()
        ex = csv.writer(sio, dialect='excel-colon')
        ex.writerow(ORDER_EXPORT_ATTRS + BOOKING_EXPORT_ATTRS)
        for order in orders_soup.query(query):
            order_attrs = list()
            for attr_name in ORDER_EXPORT_ATTRS:
                val = self.export_val(order, attr_name)
                order_attrs.append(val)
            booking_query = Eq('order_uid', order.attrs['uid'])
            for booking in bookings_soup.query(booking_query):
                booking_attrs = list()
                for attr_name in BOOKING_EXPORT_ATTRS:
                    val = self.export_val(booking, attr_name)
                    booking_attrs.append(val)
                ex.writerow(order_attrs + booking_attrs)
                booking.attrs['exported'] = True
                bookings_soup.reindex(booking)
        s_start = self.from_date.strftime('%G-%m-%d_%H-%M-%S')
        s_end = self.to_date.strftime('%G-%m-%d_%H-%M-%S')
        filename = 'orders-export-%s-%s.csv' % (s_start, s_end)
        self.request.response.setHeader('Content-Type', 'text/csv')
        self.request.response.setHeader('Content-Disposition',
                                        'attachment; filename=%s' % filename)
        return sio.getvalue().decode('utf8')


class ReservationDone(BrowserView):

    def id(self):
        uid = self.request.get('uid', None)
        try:
            order = get_order(self.context, uid)
        except ValueError:
            return None
        return order.attrs.get('ordernumber')
