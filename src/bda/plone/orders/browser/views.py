from AccessControl import Unauthorized
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from StringIO import StringIO
from bda.plone.cart import ascur
from bda.plone.checkout import message_factory as _co
from bda.plone.orders import message_factory as _
from bda.plone.orders import permissions
from bda.plone.orders.common import DT_FORMAT
from bda.plone.orders.common import OrderData
from bda.plone.orders.common import OrderTransitions
from bda.plone.orders.common import get_orders_soup
from bda.plone.orders.common import get_bookings_soup
from bda.plone.orders.common import get_order
from bda.plone.orders.common import get_vendors_for
from bda.plone.orders.common import get_vendor_uids_for
from bda.plone.orders.common import get_vendor_by_uid
from bda.plone.orders.vocabularies import customers_vocab_for
from bda.plone.orders.vocabularies import vendors_vocab_for
from bda.plone.payment import Payments
from decimal import Decimal
from node.utils import UNSET
from odict import odict
from plone.app.uuid.utils import uuidToURL
from repoze.catalog.query import Any
from repoze.catalog.query import Contains
from repoze.catalog.query import Eq
from repoze.catalog.query import Ge
from repoze.catalog.query import Le
from souper.soup import LazyRecord
from souper.soup import get_soup
from yafowil.base import ExtractionError
from yafowil.base import factory
from yafowil.controller import Controller
from yafowil.plone.form import YAMLForm
from yafowil.utils import Tag
from zope.i18n import translate
from zope.i18nmessageid import Message
import csv
import datetime
import json
import plone.api
import urllib
import uuid
import yafowil.loader  # loads registry


yafowil.loader  # pep8


class Translate(object):

    def __init__(self, request):
        self.request = request

    def __call__(self, msg):
        if not isinstance(msg, Message):
            return msg
        return translate(msg, context=self.request)


class OrderDropdown(object):
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
        ret = list()
        # lookup vendor of order, used to perform transitions
        #vendor = get_vendor_by_uid(self.record.attrs['vendor_uid'])
        vendor = self.context
        url = vendor.absolute_url()
        # create and return available transitions for order
        uid = str(self.record.attrs['uid'])
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
    'new': _('new', default=u'New'),
    'processing': _('processing', default=u'Processing'),
    'finished': _('finished', default=u'Finished'),
    'cancelled': _('cancelled', default=u'Cancelled'),
    'reserved': _('reserved', default=u'Reserved'),
}


class StateDropdown(OrderDropdown):
    name = 'state'
    css = 'dropdown change_order_state_dropdown'
    action = 'statetransition'
    vocab = state_vocab
    transitions = {
        'renew': _('renew', default=u'Renew'),
        'process': _('process', default=u'Process'),
        'finish': _('finish', default=u'Finish'),
        'cancel': _('cancel', default=u'Cancel'),
    }

    @property
    def value(self):
        return self.record.attrs['state']

    @property
    def items(self):
        state = self.record.attrs['state']
        transitions = list()
        if state in ['new', 'reserved']:
            transitions = ['process', 'finish', 'cancel']
        else:
            transitions = ['renew']
        return self.create_items(transitions)


salaried_vocab = {
    'yes': _('yes', default=u'Yes'),
    'no': _('no', default=u'No'),
    'failed': _('failed', default=u'Failed'),
}


class SalariedDropdown(OrderDropdown):
    name = 'salaried'
    css = 'dropdown change_order_salaried_dropdown'
    action = 'salariedtransition'
    vocab = salaried_vocab
    transitions = {
        'mark_salaried': _('mark_salaried', default=u'Mark salaried'),
        'mark_outstanding': _('mark_outstanding', default=u'Mark outstanding'),
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
        order = get_order(self.context, uid)
        vendor = get_vendor_by_uid(order.attrs['vendor_uid'])
        user = plone.api.user.get_current()
        if not user.checkPermission(permissions.ModifyOrders, vendor):
            raise Unauthorized
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
            'head': callback,
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


class OrdersViewBase(BrowserView):
    table_view_name = '@@orderstable'

    def orders_table(self):
        return self.context.restrictedTraverse(self.table_view_name)()


class OrdersView(OrdersViewBase):

    def __call__(self):
        # check if authenticated user is vendor
        if not get_vendors_for():
            raise Unauthorized
        return super(OrdersView, self).__call__()


class MyOrdersView(OrdersViewBase):
    table_view_name = '@@myorderstable'


class OrdersTableBase(BrowserView):
    table_template = ViewPageTemplateFile('table.pt')
    table_id = 'bdaploneorders'
    data_view_name = '@@ordersdata'

    def rendered_table(self):
        return self.table_template(self)

    def render_filter(self):
        return None

    def render_order_actions_head(self):
        return None

    def render_order_actions(self, colname, record):
        return None

    def render_salaried(self, colname, record):
        return record.attrs.get('salaried', 'no')

    def render_state(self, colname, record):
        return record.attrs['state']

    def render_dt(self, colname, record):
        value = record.attrs.get(colname, '')
        if value:
            value = value.strftime(DT_FORMAT)
        return value

    @property
    def ajaxurl(self):
        site = plone.api.portal.get()
        return '%s/%s' % (site.absolute_url(), self.data_view_name)

    @property
    def columns(self):
        return [{
            'id': 'actions',
            'label': _('actions', default=u'Actions'),
            'head': self.render_order_actions_head,
            'renderer': self.render_order_actions,
        }, {
            'id': 'created',
            'label': _('date', default=u'Date'),
            'renderer': self.render_dt,
        }, {
            'id': 'personal_data.lastname',
            'label': _('lastname', default=u'Last Name'),
        }, {
            'id': 'personal_data.firstname',
            'label': _('firstname', default=u'First Name'),
        }, {
            'id': 'billing_address.city',
            'label': _('city', default=u'City'),
        }, {
            'id': 'salaried',
            'label': _('salaried', default=u'Salaried'),
            'renderer': self.render_salaried,
        }, {
            'id': 'state',
            'label': _('state', default=u'State'),
            'renderer': self.render_state,
        }]


def vendors_form_vocab():
    vendors = vendors_vocab_for()
    return [('', _('all', default='All'))] + vendors


def customers_form_vocab():
    customers = customers_vocab_for()
    return [('', _('all', default='All'))] + customers


class OrdersTable(OrdersTableBase):

    def render_filter(self):
        # vendor areas of current user
        vendors = vendors_form_vocab()
        vendor_selector = None
        # vendor selection, include if more than one vendor
        if len(vendors) > 2:
            vendor_selector = factory(
                'label:select',
                name='vendor',
                value=self.request.form.get('ordersfilter.vendor', UNSET),
                props={
                    'vocabulary': vendors,
                    'label': 'Filter for vendors'
                }
            )
        # customers of current user
        customers = customers_form_vocab()
        customer_selector = None
        # customers selection, include if more than one customer
        if len(customers) > 2:
            customer_selector = factory(
                'label:select',
                name='customer',
                value=self.request.form.get('ordersfilter.customer', UNSET),
                props={
                    'vocabulary': customers,
                    'label': 'Filter for customers'
                }
            )
        if not vendor_selector and not customer_selector:
            return
        # create filter form
        action = self.request.getURL()
        form = factory(
            'form',
            name='ordersfilter',
            props={'action': action},
        )
        if vendor_selector:
            form['vendor'] = vendor_selector
        if customer_selector:
            form['customer'] = customer_selector
        form['submit'] = factory(
            'submit',
            name='filter',
            props={'action': True, 'label': 'Filter'}
        )
        return form(request=self.request)

    def render_order_actions_head(self):
        tag = Tag(Translate(self.request))
        select_all_orders_attrs = {
            'name': 'select_all_orders',
            'type': 'checkbox',
            'class_': 'select_all_orders',
            'title': _('select_all_orders',
                       default=u'Select all visible orders'),
        }
        select_all_orders = tag('input', **select_all_orders_attrs)
        notify_customers_target = self.context.absolute_url()
        notify_customers_attributes = {
            'ajax:target': notify_customers_target,
            'class_': 'notify_customers',
            'href': '',
            'title': _('notify_customers',
                       default=u'Notify customers of selected orders'),
        }
        notify_customers = tag('a', '&nbsp', **notify_customers_attributes)
        return select_all_orders + notify_customers

    def render_order_actions(self, colname, record):
        tag = Tag(Translate(self.request))
        view_order_target = '%s?uid=%s' % (
            self.context.absolute_url(), str(record.attrs['uid']))
        view_order_attrs = {
            'ajax:bind': 'click',
            'ajax:target': view_order_target,
            'ajax:overlay': 'order',
            'class_': 'contenttype-document',
            'href': '',
            'title': _('view_order', default=u'View Order'),
        }
        view_order = tag('a', '&nbsp', **view_order_attrs)
        select_order_attrs = {
            'name': 'select_order',
            'type': 'checkbox',
            'value': record.attrs['uid'],
            'class_': 'select_order',
        }
        select_order = tag('input', **select_order_attrs)
        return select_order + view_order

    def check_modify_order(self, order):
        return True
        # XXX: crap
        #vendor = get_vendor_by_uid(order.attrs['vendor_uid'])
        #user = plone.api.user.get_current()
        #if user.checkPermission(permissions.ModifyOrders, vendor):
        #    return True

    def render_salaried(self, colname, record):
        if not self.check_modify_order(record):
            return record.attrs['salaried']
        return SalariedDropdown(self.context, self.request, record).render()

    def render_state(self, colname, record):
        if not self.check_modify_order(record):
            return record.attrs['state']
        return StateDropdown(self.context, self.request, record).render()

    @property
    def ajaxurl(self):
        params = [
            ('vendor', self.request.form.get('ordersfilter.vendor')),
            ('customer', self.request.form.get('ordersfilter.customer'))
        ]
        query = urllib.urlencode(dict([it for it in params if it[1]]))
        query = query and '?{0}'.format(query) or ''
        site = plone.api.portal.get()
        return '%s/%s%s' % (site.absolute_url(), self.data_view_name, query)

    def __call__(self):
        # check if authenticated user is vendor
        if not get_vendors_for():
            raise Unauthorized
        #self.vendor_uids = get_vendor_uids_for()
        #if not self.vendor_uids:
        #    raise Unauthorized
        return super(OrdersTable, self).__call__()


class MyOrdersTable(OrdersTableBase):
    data_view_name = '@@myordersdata'

    def render_order_actions(self, colname, record):
        tag = Tag(Translate(self.request))
        view_order_target = '%s?uid=%s' % (
            self.context.absolute_url(), str(record.attrs['uid']))
        view_order_attrs = {
            'ajax:bind': 'click',
            'ajax:target': view_order_target,
            'ajax:overlay': 'myorder',
            'class_': 'contenttype-document',
            'href': '',
            'title': _('view_order', default=u'View Order'),
        }
        view_order = tag('a', '&nbsp', **view_order_attrs)
        return view_order


class OrdersData(OrdersTable, TableData):
    soup_name = 'bda_plone_orders_orders'
    search_text_index = 'text'

    def query(self, soup):
        # fetch user vendor uids
        vendor_uids = get_vendor_uids_for()
        # filter by given vendor uid or user vendor uids
        vendor_uid = self.request.form.get('vendor')
        if vendor_uid:
            vendor_uid = uuid.UUID(vendor_uid)
            # raise if given vendor uid not in user vendor uids
            if not vendor_uid in vendor_uids:
                raise Unauthorized
            query = Any('vendor_uids', [vendor_uid])
        else:
            query = Any('vendor_uids', vendor_uids)
        # filter by customer if given
        customer = self.request.form.get('customer')
        if customer:
            query = query & Eq('creator', customer)
        # filter by search term if given
        term = self.request.form['sSearch'].decode('utf-8')
        if term:
            query = query & Contains(self.search_text_index, term)
        # query orders and return result
        sort = self.sort()
        res = soup.lazy(query,
                        sort_index=sort['index'],
                        reverse=sort['reverse'],
                        with_size=True)
        length = res.next()
        return length, res


class MyOrdersData(MyOrdersTable, TableData):
    soup_name = 'bda_plone_orders_orders'
    search_text_index = 'text'

    def query(self, soup):
        query = Eq('creator', plone.api.user.get_current().getId())
        # filter by search term if given
        term = self.request.form['sSearch'].decode('utf-8')
        if term:
            query = query & Contains(self.search_text_index, term)
        # query orders and return result
        sort = self.sort()
        res = soup.lazy(query,
                        sort_index=sort['index'],
                        reverse=sort['reverse'],
                        with_size=True)
        length = res.next()
        return length, res


class OrderViewBase(BrowserView):

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
                'url': uuidToURL(booking.attrs['buyable_uid']),
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
            return _('none', default=u'None')
        return tid

    def state(self, order):
        return state_vocab[order.get('state', 'new')]

    def created(self, order):
        value = order.get('created', _('unknown', default=u'Unknown'))
        if value:
            value = value.strftime(DT_FORMAT)
        return value

    def exported(self, item):
        return item['exported'] \
            and _('yes', default=u'Yes') or _('no', default=u'No')


class OrderView(OrderViewBase):

    def __call__(self):
        # check if authenticated user is vendor
        self.vendor_uids = get_vendor_uids_for()
        if not self.vendor_uids:
            raise Unauthorized
        return super(OrderView, self).__call__()

    @property
    def order_data(self):
        return OrderData(self.context,
                         uid=self.uid,
                         vendor_uids=self.vendor_uids)


class MyOrderView(OrderViewBase):

    def __call__(self):
        # check if order was created by authenticated user
        user = plone.api.user.get_current()
        if user.getId() != self.order['creator']:
            raise Unauthorized
        return super(MyOrderView, self).__call__()


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
COMPUTER_ORDER_EXPORT_ATTRS = odict()
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
COMPUTER_BOOKING_EXPORT_ATTRS = odict()


def resolve_buyable_url(context, booking):
    return uuidToURL(booking.attrs['buyable_uid'])

COMPUTER_BOOKING_EXPORT_ATTRS['url'] = resolve_buyable_url


class ExportOrdersForm(YAMLForm):
    browser_template = ViewPageTemplateFile('export.pt')
    form_template = 'bda.plone.orders.browser:forms/orders_export.yaml'
    message_factory = _
    action_resource = 'exportorders'

    def __call__(self):
        # check if authenticated user is vendor
        if not get_vendors_for():
            raise Unauthorized
        self.prepare()
        controller = Controller(self.form, self.request)
        if not controller.next:
            self.rendered_form = controller.rendered
            return self.browser_template(self)
        return controller.next

    def vendor_vocabulary(self):
        return vendors_form_vocab()

    def vendor_mode(self):
        return len(vendors_form_vocab()) > 2 and 'edit' or 'skip'

    def customer_vocabulary(self):
        return customers_form_vocab()

    def customer_mode(self):
        return len(customers_form_vocab()) > 2 and 'edit' or 'skip'

    def from_before_to(self, widget, data):
        from_date = data.fetch('exportorders.from').extracted
        to_date = data.fetch('exportorders.to').extracted
        if to_date <= from_date:
            raise ExtractionError(_('from_date_before_to_date',
                                    default=u'From-date after to-date'))
        return data.extracted

    def export(self, widget, data):
        self.vendor = self.request.form.get('exportorders.vendor')
        self.customer = self.request.form.get('exportorders.customer')
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
        # get orders soup
        orders_soup = get_orders_soup(self.context)
        # get bookings soup
        bookings_soup = get_bookings_soup(self.context)
        # fetch user vendor uids
        vendor_uids = get_vendor_uids_for()
        # base query for time range
        query = Ge('created', self.from_date) & Le('created', self.to_date)
        # filter by given vendor uid or user vendor uids
        vendor_uid = self.vendor
        if vendor_uid:
            vendor_uid = uuid.UUID(vendor_uid)
            # raise if given vendor uid not in user vendor uids
            if not vendor_uid in vendor_uids:
                raise Unauthorized
            query = Any('vendor_uids', [vendor_uid])
        else:
            query = Any('vendor_uids', vendor_uids)
        # filter by customer if given
        customer = self.customer
        if customer:
            query = query & Eq('creator', customer)
        # prepare csv writer
        sio = StringIO()
        ex = csv.writer(sio, dialect='excel-colon')
        # exported column keys as first line
        ex.writerow(ORDER_EXPORT_ATTRS +
                    COMPUTER_ORDER_EXPORT_ATTRS.keys() +
                    BOOKING_EXPORT_ATTRS +
                    COMPUTER_BOOKING_EXPORT_ATTRS.keys())
        # query orders
        for order in orders_soup.query(query):
            order_attrs = list()
            # order export attrs
            for attr_name in ORDER_EXPORT_ATTRS:
                val = self.export_val(order, attr_name)
                order_attrs.append(val)
            # computed order export attrs
            for attr_name in COMPUTER_ORDER_EXPORT_ATTRS:
                cb = COMPUTER_ORDER_EXPORT_ATTRS[attr_name]
                val = cb(self.context, order)
                order_attrs.append(val)
            # only order bookings for current vendor_uids
            order_data = OrderData(order=order, vendor_uids=vendor_uids)
            for booking in order_data.bookings:
                booking_attrs = list()
                # booking export attrs
                for attr_name in BOOKING_EXPORT_ATTRS:
                    val = self.export_val(booking, attr_name)
                    booking_attrs.append(val)
                # computed booking export attrs
                for attr_name in COMPUTER_BOOKING_EXPORT_ATTRS:
                    cb = COMPUTER_ORDER_EXPORT_ATTRS[attr_name]
                    val = cb(self.context, booking)
                    booking_attrs.append(val)
                ex.writerow(order_attrs + booking_attrs)
                booking.attrs['exported'] = True
                bookings_soup.reindex(booking)
        # create and return response
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
