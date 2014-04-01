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
from bda.plone.orders import vocabularies as vocabs
from bda.plone.orders import interfaces as ifaces
from bda.plone.payment import Payments
from decimal import Decimal
from node.utils import UNSET
from odict import odict
from plone.app.uuid.utils import uuidToURL
from plone.memoize import view
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

    @property
    def order_data(self):
        vendor_uid = self.request.form.get('vendor', '')
        if vendor_uid:
            vendor_uids = [vendor_uid]
        else:
            vendor_uids = get_vendor_uids_for()
        return OrderData(self.context,
                         order=self.record,
                         vendor_uids=vendor_uids)

    def create_items(self, transitions):
        ret = list()
        url = self.context.absolute_url()
        # create and return available transitions for order
        uid = str(self.record.attrs['uid'])
        vendor = self.request.form.get('vendor', '')
        for transition in transitions:
            if vendor:
                target = '%s?transition=%s&uid=%s&vendor=%s' % (
                    url, transition, uid, vendor)
            else:
                target = '%s?transition=%s&uid=%s' % (url, transition, uid)
            ret.append({
                'title': self.transitions[transition],
                'target': target,
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


class StateDropdown(OrderDropdown):
    name = 'state'
    css = 'dropdown change_order_state_dropdown'
    action = 'statetransition'
    vocab = vocabs.state_vocab()
    transitions = vocabs.state_transitions_vocab()

    @property
    def value(self):
        return self.order_data.state

    @property
    def items(self):
        state = self.order_data.state
        transitions = list()
        if state in [ifaces.STATE_NEW, ifaces.STATE_RESERVED]:
            transitions = [
                ifaces.STATE_TRANSITION_PROCESS,
                ifaces.STATE_TRANSITION_FINISH,
                ifaces.STATE_TRANSITION_CANCEL
            ]
        elif state == ifaces.STATE_MIXED:
            transitions = [
                ifaces.STATE_TRANSITION_PROCESS,
                ifaces.STATE_TRANSITION_FINISH,
                ifaces.STATE_TRANSITION_CANCEL,
                ifaces.STATE_TRANSITION_RENEW
            ]
        elif state == ifaces.STATE_PROCESSING:
            transitions = [
                ifaces.STATE_TRANSITION_FINISH,
                ifaces.STATE_TRANSITION_CANCEL,
                ifaces.STATE_TRANSITION_RENEW
            ]
        else:
            transitions = [ifaces.STATE_TRANSITION_RENEW]
        return self.create_items(transitions)


class SalariedDropdown(OrderDropdown):
    name = 'salaried'
    css = 'dropdown change_order_salaried_dropdown'
    action = 'salariedtransition'
    vocab = vocabs.salaried_vocab()
    transitions = vocabs.salaried_transitions_vocab()

    @property
    def value(self):
        return self.order_data.salaried or ifaces.SALARIED_NO

    @property
    def items(self):
        salaried = self.order_data.salaried or ifaces.SALARIED_NO
        transitions = []
        if salaried == ifaces.SALARIED_YES:
            transitions = [ifaces.SALARIED_TRANSITION_OUTSTANDING]
        elif salaried == ifaces.SALARIED_NO:
            transitions = [ifaces.SALARIED_TRANSITION_SALARIED]
        else:
            transitions = [
                ifaces.SALARIED_TRANSITION_OUTSTANDING,
                ifaces.SALARIED_TRANSITION_SALARIED
            ]
        return self.create_items(transitions)


class Transition(BrowserView):
    dropdown = None

    def __call__(self):
        transition = self.request['transition']
        uid = self.request['uid']
        order = get_order(self.context, uid)
        vendor_uid = self.request.form.get('vendor', '')
        if vendor_uid:
            vendor_uids = [vendor_uid]
            vendor = get_vendor_by_uid(self.context, vendor_uid)
            user = plone.api.user.get_current()
            if not user.checkPermission(permissions.ModifyOrders, vendor):
                raise Unauthorized
        else:
            vendor_uids = get_vendor_uids_for()
            if not vendor_uids:
                raise Unauthorized
        transitions = OrderTransitions(self.context)
        order = transitions.do_transition(uid, vendor_uids, transition)
        return self.dropdown(self.context, self.request, order).render()


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
        return OrderData(self.context, order=record).salaried\
            or ifaces.SALARIED_NO

    def render_state(self, colname, record):
        return OrderData(self.context, order=record).state

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
    vendors = vocabs.vendors_vocab_for()
    return [('', _('all', default='All'))] + vendors


def customers_form_vocab():
    customers = vocabs.customers_vocab_for()
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
                value=self.request.form.get('vendor', ''),
                props={
                    'vocabulary': vendors,
                    'label': _('filter_for_vendors',
                               default=u'Filter for vendors'),
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
                value=self.request.form.get('customer', ''),
                props={
                    'vocabulary': customers,
                    'label': _('filter_for_customers',
                               default=u'Filter for customers'),
                }
            )
        if not vendor_selector and not customer_selector:
            return
        # concatenate filters
        filter = ''
        if vendor_selector:
            filter += vendor_selector(request=self.request)
        if customer_selector:
            filter += customer_selector(request=self.request)
        return filter

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
        vendor_uid = self.request.form.get('vendor', '')
        if vendor_uid:
            view_order_target = '%s?uid=%s&vendor=%s' % (
                self.context.absolute_url(),
                str(record.attrs['uid']),
                vendor_uid)
        else:
            view_order_target = '%s?uid=%s' % (
                self.context.absolute_url(),
                str(record.attrs['uid']))
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
        vendor_uid = self.request.form.get('vendor', '')
        if vendor_uid:
            vendor_uids = [vendor_uid]
            vendor = get_vendor_by_uid(self.context, vendor_uid)
            user = plone.api.user.get_current()
            if not user.checkPermission(permissions.ModifyOrders, vendor):
                return False
        else:
            vendor_uids = get_vendor_uids_for()
            if not vendor_uids:
                return False
        return True

    def render_salaried(self, colname, record):
        if not self.check_modify_order(record):
            return OrderData(self.context, order=record).salaried
        return SalariedDropdown(self.context, self.request, record).render()

    def render_state(self, colname, record):
        if not self.check_modify_order(record):
            return OrderData(self.context, order=record).state
        return StateDropdown(self.context, self.request, record).render()

    @property
    def ajaxurl(self):
        params = [
            ('vendor', self.request.form.get('vendor')),
            ('customer', self.request.form.get('customer'))
        ]
        query = urllib.urlencode(dict([it for it in params if it[1]]))
        query = query and '?{0}'.format(query) or ''
        site = plone.api.portal.get()
        return '%s/%s%s' % (site.absolute_url(), self.data_view_name, query)

    def __call__(self):
        # check if authenticated user is vendor
        if not get_vendors_for():
            raise Unauthorized
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
        view_order = tag('a', '&nbsp;', **view_order_attrs)
        self.request.response.setHeader("Content-type", "application/json")
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
        self.request.response.setHeader("Content-type", "application/json")
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
    @view.memoize
    def order_data(self):
        return OrderData(self.context, uid=self.uid)

    @property
    def uid(self):
        return self.request.form['uid']

    @property
    def order(self):
        return dict(self.order_data.order.attrs)

    @property
    def net(self):
        return ascur(self.order_data.net)

    @property
    def vat(self):
        return ascur(self.order_data.vat)

    @property
    def discount_net(self):
        return ascur(self.order_data.discount_net)

    @property
    def discount_vat(self):
        return ascur(self.order_data.discount_vat)

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
        # XXX: discount
        ret = list()
        for booking in self.order_data.bookings:
            ret.append({
                'title': booking.attrs['title'],
                'url': uuidToURL(booking.attrs['buyable_uid']),
                'count': booking.attrs['buyable_count'],
                'net': ascur(booking.attrs.get('net', 0.0)),
                'discount_net': ascur(float(booking.attrs['discount_net'])),
                'vat': booking.attrs.get('vat', 0.0),
                'exported': booking.attrs['exported'],
                'comment': booking.attrs['buyable_comment'],
                'quantity_unit': booking.attrs.get('quantity_unit'),
                'currency': booking.attrs.get('currency'),
            })
        return ret

    @property
    def gender(self):
        gender = self.order['personal_data.gender']
        if gender == 'male':
            return _co('male', 'Male')
        if gender == 'female':
            return _co('female', 'Female')
        return gender

    @property
    def payment(self):
        name = self.order['payment_selection.payment']
        payment = Payments(self.context).get(name)
        if payment:
            return payment.label
        return name

    @property
    def salaried(self):
        salaried = self.order_data.salaried or ifaces.SALARIED_NO
        return vocabs.salaried_vocab()[salaried]

    @property
    def tid(self):
        tid = self.order_data.tid or 'none'
        if tid == 'none':
            return _('none', default=u'None')
        return tid

    @property
    def state(self):
        state = self.order_data.state or ifaces.STATE_NEW
        return vocabs.state_vocab()[state]

    @property
    def created(self):
        value = self.order.get('created', _('unknown', default=u'Unknown'))
        if value:
            value = value.strftime(DT_FORMAT)
        return value

    def exported(self, item):
        return item['exported'] \
            and _('yes', default=u'Yes') or _('no', default=u'No')


class OrderView(OrderViewBase):

    def __call__(self):
        vendor_uid = self.request.form.get('vendor', '')
        if vendor_uid:
            self.vendor_uids = [vendor_uid]
            vendor = get_vendor_by_uid(self.context, vendor_uid)
            user = plone.api.user.get_current()
            if not user.checkPermission(permissions.ModifyOrders, vendor):
                raise Unauthorized
        else:
            self.vendor_uids = get_vendor_uids_for()
            if not self.vendor_uids:
                raise Unauthorized
        return super(OrderView, self).__call__()

    @property
    @view.memoize
    def order_data(self):
        return OrderData(
            self.context,
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
    'cart_discount_net',
    'cart_discount_vat',
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
COMPUTED_ORDER_EXPORT_ATTRS = odict()
BOOKING_EXPORT_ATTRS = [
    'title',
    'buyable_comment',
    'buyable_count',
    'quantity_unit',
    'net',
    'discount_net',
    'vat',
    'currency',
    'state',
    'salaried',
    'exported',
]
COMPUTED_BOOKING_EXPORT_ATTRS = odict()


def resolve_buyable_url(context, booking):
    return uuidToURL(booking.attrs['buyable_uid'])

COMPUTED_BOOKING_EXPORT_ATTRS['url'] = resolve_buyable_url


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
            query = query & Any('vendor_uids', [vendor_uid])
        else:
            query = query & Any('vendor_uids', vendor_uids)
        # filter by customer if given
        customer = self.customer
        if customer:
            query = query & Eq('creator', customer)
        # prepare csv writer
        sio = StringIO()
        ex = csv.writer(sio, dialect='excel-colon')
        # exported column keys as first line
        ex.writerow(ORDER_EXPORT_ATTRS +
                    COMPUTED_ORDER_EXPORT_ATTRS.keys() +
                    BOOKING_EXPORT_ATTRS +
                    COMPUTED_BOOKING_EXPORT_ATTRS.keys())
        # query orders
        for order in orders_soup.query(query):
            # restrict order bookings for current vendor_uids
            order_data = OrderData(self.context,
                                   order=order,
                                   vendor_uids=vendor_uids)
            order_attrs = list()
            # order export attrs
            for attr_name in ORDER_EXPORT_ATTRS:
                val = self.export_val(order, attr_name)
                order_attrs.append(val)
            # computed order export attrs
            for attr_name in COMPUTED_ORDER_EXPORT_ATTRS:
                cb = COMPUTED_ORDER_EXPORT_ATTRS[attr_name]
                val = cb(self.context, order_data)
                order_attrs.append(val)
            for booking in order_data.bookings:
                booking_attrs = list()
                # booking export attrs
                for attr_name in BOOKING_EXPORT_ATTRS:
                    val = self.export_val(booking, attr_name)
                    booking_attrs.append(val)
                # computed booking export attrs
                for attr_name in COMPUTED_BOOKING_EXPORT_ATTRS:
                    cb = COMPUTED_BOOKING_EXPORT_ATTRS[attr_name]
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
