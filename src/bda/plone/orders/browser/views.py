import json
import uuid
import csv
import datetime
from StringIO import StringIO
from zope.i18n import translate
from zope.i18nmessageid import (
    Message,
    MessageFactory,
)
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from repoze.catalog.query import (
    Contains,
    Eq,
    Ge,
    Le,
)
from souper.soup import (
    get_soup,
    LazyRecord,
)
from yafowil.utils import Tag
from yafowil.plone.form import YAMLForm
from bda.plone.cart import ascur
from ..common import (
    DT_FORMAT,
    get_order,
    OrderTransitions,
)

_ = MessageFactory('bda.plone.orders')
_co = MessageFactory('bda.plone.checkout')
_pa = MessageFactory('bda.plone.payment')


def message(context, msg):
    putils = getToolByName(context, 'plone_utils')
    putils.addPortalMessage(msg)


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
        if state == 'new':
            transitions = ['finish', 'cancel']
        else:
            transitions = ['renew']
        return self.create_items(transitions)


class SalariedDropdown(Dropdown):
    name = 'salaried'
    css = 'dropdown change_order_salaried_dropdown'
    action = 'salariedtransition'
    vocab = {
        'yes': _('yes', 'Yes'),
        'no': _('no', 'No'),
    }
    transitions = {
        'mark_salaried': _('mark_salaried', 'Mark salaried'),
        'mark_outstanding': _('mark_outstanding', 'Mark outstanding'),
    }
    
    @property
    def value(self):
        return self.record.attrs.get('salaried') == 'yes' and 'yes' or 'no'
    
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
            'id': 'personal_data.surname',
            'label': _('surname', 'Surname'),
        }, {
            'id': 'personal_data.name',
            'label': _('name', 'Name'),
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
        columns = self.columns
        sort = self.sort()
        term = self.request.form['sSearch']
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
        return uuid.UUID(self.request.form['uid'])
    
    @property
    def order(self):
        record = get_order(self.context, self.uid)
        return dict(record.attrs)
    
    @property
    def bookings(self):
        soup = get_soup('bda_plone_orders_bookings', self.context)
        return soup.query(Eq('order_uid', self.uid))
    
    @property
    def net(self):
        ret = 0.0
        for booking in self.bookings:
            count = float(booking.attrs['buyable_count'])
            ret += booking.attrs.get('net', 0.0) * count
        return ascur(ret)
    
    @property
    def vat(self):
        ret = 0.0
        for booking in self.bookings:
            count = float(booking.attrs['buyable_count'])
            net = booking.attrs.get('net', 0.0) * count
            ret += net * booking.attrs.get('vat', 0.0) / 100
        return ascur(ret)
    
    @property
    def total(self):
        ret = 0.0
        for booking in self.bookings:
            count = float(booking.attrs['buyable_count'])
            net = booking.attrs.get('net', 0.0) * count
            ret += net
            ret += net * booking.attrs.get('vat', 0.0) / 100
        return ascur(ret)
    
    @property
    def listing(self):
        ret = list()
        for booking in self.bookings:
            ret.append({
                'title': booking.attrs['title'],
                'count': booking.attrs['buyable_count'],
                'net': ascur(booking.attrs.get('net', 0.0)),
                'vat': booking.attrs.get('vat', 0.0),
                'exported': booking.attrs['exported'],
                'comment': booking.attrs['buyable_comment'],
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
        payment = order['payment_selection.payment']
        return payment == 'credit_card' \
            and _pa('credit_card', 'Credit Card') \
            or _pa('invoice', 'Invoice')
    
    def salaried(self, order):
        return order.get('salaried') == 'yes' \
            and _('yes', 'Yes') or _('no', 'No')
    
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


class ExportOrdersForm(YAMLForm):
    form_template = 'bda.plone.orders.browser:forms/orders_export.yaml'
    message_factory = _
    action_resource = 'exportorders'
    
    def export(self, widget, data):
        self.from_date = data.fetch('exportorders.from').extracted
        self.to_date = data.fetch('exportorders.to').extracted
    
    def csv(self, request):
        orders_soup = get_soup('bda_plone_orders_orders', self.context)
        bookings_soup = get_soup('bda_plone_orders_bookings', self.context)
        query = Ge('created', self.from_date) & Le('created', self.to_date)
        order_attr_blacklist = ['booking_uids', 'creator']
        booking_attrs = ['buyable_count', 'buyable_comment', 'exported',
                         'title', 'net', 'vat']
        sio = StringIO()
        ex = csv.writer(sio, dialect='excel-colon')
        for order in orders_soup.query(query):
            row = list()
            keys = sorted(order.attrs.keys())
            for key in keys:
                if key in order_attr_blacklist:
                    continue
                val = order.attrs[key]
                if isinstance(val, datetime.datetime):
                    val = val.strftime(DT_FORMAT)
                row.append(val)
            booking_query = Eq('order_uid', order.attrs['uid'])
            for booking in bookings_soup.query(booking_query):
                booking_attrs = list()
                for key in booking_attrs:
                    val = order.attrs.get(key)
                    if isinstance(val, datetime.datetime):
                        val = val.strftime(DT_FORMAT)
                    booking_attrs.append(val)
                ex.writerow(row + booking_attrs)
                booking.attrs['exported'] = True
                bookings_soup.reindex(booking)
        s_start = self.from_date.strftime('%G-%m-%d_%H-%M-%S') 
        s_end = self.to_date.strftime('%G-%m-%d_%H-%M-%S')
        filename = 'orders-export-%s-%s.csv' % (s_start, s_end) 
        self.request.response.setHeader('Content-Type', 'text/csv')
        self.request.response.setHeader('Content-Disposition', 
                                        'attachment; filename=%s' % filename)
        return sio.getvalue().decode('utf8')