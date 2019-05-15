# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from bda.plone.orders import interfaces as ifaces
from bda.plone.orders import message_factory as _
from bda.plone.orders import permissions
from bda.plone.orders import vocabularies as vocabs
from bda.plone.orders.browser.common import customers_form_vocab
from bda.plone.orders.browser.common import salaried_form_vocab
from bda.plone.orders.browser.common import states_form_vocab
from bda.plone.orders.browser.common import Transition
from bda.plone.orders.browser.common import Translate
from bda.plone.orders.browser.common import vendors_form_vocab
from bda.plone.orders.browser.dropdown import BaseDropdown
from bda.plone.orders.common import DT_FORMAT
from bda.plone.orders.common import get_vendor_by_uid
from bda.plone.orders.common import get_vendor_uids_for
from bda.plone.orders.common import get_vendors_for
from bda.plone.orders.common import OrderData
from bda.plone.orders.interfaces import IBuyable
from bda.plone.orders.transitions import do_transition_for
from bda.plone.orders.transitions import transitions_of_main_state
from bda.plone.orders.transitions import transitions_of_salaried_state
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.resources import add_bundle_on_request
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from repoze.catalog.query import Any
from repoze.catalog.query import Contains
from repoze.catalog.query import Eq
from souper.soup import get_soup
from souper.soup import LazyRecord
from yafowil.base import factory
from yafowil.utils import Tag
from zope.i18n import translate

import json
import plone.api
import six.moves.urllib.parse
import uuid


###############################################################################
# orders table base
###############################################################################


class TableData(BrowserView):
    """Base view for displaying sour records in datatable.
    """

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
        raise NotImplementedError(
            u"Abstract DataTable does not implement " u"``columns``."
        )

    def query(self, soup):
        """Return 2-tuple with result length and lazy record iterator.
        """
        raise NotImplementedError(
            u"Abstract DataTable does not implement " u"``query``."
        )

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
        iids = sort_index.sort(list(data.keys()), reverse=sort['reverse'])

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
        # XXX: include JSON response header

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
        self.request.response.setHeader("Content-type", "application/json")
        return json.dumps(data)


###############################################################################
# order related dropdowns and transitions
###############################################################################


class OrderDropdown(BaseDropdown):
    @property
    def order_data(self):
        vendor_uid = self.request.form.get('vendor', '')
        if vendor_uid:
            vendor_uids = [vendor_uid]
        else:
            vendor_uids = get_vendor_uids_for()
        return OrderData(self.context, order=self.record, vendor_uids=vendor_uids)


class OrderStateDropdown(OrderDropdown):
    name = 'state'
    css = 'dropdown change_order_state_dropdown'
    action = 'orderstatetransition'
    vocab = vocabs.state_vocab()
    transitions = vocabs.state_transitions_vocab()

    @property
    def value(self):
        return self.order_data.state

    @property
    def items(self):
        transitions = transitions_of_main_state(self.value)
        return self.create_items(transitions)


class OrderSalariedDropdown(OrderDropdown):
    name = 'salaried'
    css = 'dropdown change_order_salaried_dropdown'
    action = 'ordersalariedtransition'
    vocab = vocabs.salaried_vocab()
    transitions = vocabs.salaried_transitions_vocab()

    @property
    def value(self):
        return self.order_data.salaried or ifaces.SALARIED_NO

    @property
    def items(self):
        transitions = transitions_of_salaried_state(self.value)
        return self.create_items(transitions)


class OrderTransition(Transition):
    def do_transition(self, uid, transition, vendor_uids):
        order_data = OrderData(self.context, uid=uid, vendor_uids=vendor_uids)
        do_transition_for(
            order_data,
            transition=transition,
            context=self.context,
            request=self.request,
        )
        return order_data.order


class OrderStateTransition(OrderTransition):
    dropdown = OrderStateDropdown


class OrderSalariedTransition(OrderTransition):
    dropdown = OrderSalariedDropdown


class OrdersViewBase(BrowserView):
    table_view_name = '@@orderstable'

    def __init__(self, context, request):
        super(OrdersViewBase, self).__init__(context, request)
        add_bundle_on_request(request, 'bdajax-jquerytools')
        add_bundle_on_request(request, 'bdajax-jquerytools-overlay')
        add_bundle_on_request(request, 'datatables')
        add_bundle_on_request(request, 'bda-plone-orders')

    def orders_table(self):
        return self.context.restrictedTraverse(self.table_view_name)()


###############################################################################
# orders views
###############################################################################


class OrdersView(OrdersViewBase):
    def __call__(self):
        # check if authenticated user is vendor
        if not get_vendors_for():
            raise Unauthorized
        return super(OrdersView, self).__call__()


class MyOrdersView(OrdersViewBase):
    table_view_name = '@@myorderstable'


class OrdersTableBase(BrowserView):
    table_template = ViewPageTemplateFile('templates/table.pt')
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
        salaried = OrderData(self.context, order=record).salaried or ifaces.SALARIED_NO
        return translate(vocabs.salaried_vocab()[salaried], context=self.request)

    def render_state(self, colname, record):
        state = OrderData(self.context, order=record).state
        if not state:
            return '-/-'
        return translate(vocabs.state_vocab()[state], context=self.request)

    def render_dt(self, colname, record):
        value = record.attrs.get(colname, '')
        if value:
            value = value.strftime(DT_FORMAT)
        return value

    @property
    def ajaxurl(self):
        return u'{0}/{1}'.format(self.context.absolute_url(), self.data_view_name)

    @property
    def columns(self):
        return [
            {
                'id': 'actions',
                'label': _('actions', default=u'Actions'),
                'head': self.render_order_actions_head,
                'renderer': self.render_order_actions,
            },
            {
                'id': 'created',
                'label': _('date', default=u'Date'),
                'renderer': self.render_dt,
            },
            {
                'id': 'personal_data.lastname',
                'label': _('lastname', default=u'Last Name'),
            },
            {
                'id': 'personal_data.firstname',
                'label': _('firstname', default=u'First Name'),
            },
            {'id': 'personal_data.email', 'label': _('email', default=u'Email')},
            {'id': 'billing_address.city', 'label': _('city', default=u'City')},
            {
                'id': 'salaried',
                'label': _('salaried', default=u'Salaried'),
                'renderer': self.render_salaried,
            },
            {
                'id': 'state',
                'label': _('state', default=u'State'),
                'renderer': self.render_state,
            },
        ]


class OrdersTable(OrdersTableBase):
    def render_filter(self):
        # vendor areas of current user
        vendors = vendors_form_vocab()
        vendor_selector = None
        # vendor selection, include if more than one vendor
        if len(vendors) > 2:
            vendor_selector = factory(
                'div:label:select',
                name='vendor',
                value=self.request.form.get('vendor', ''),
                props={
                    'vocabulary': vendors,
                    'label': _('filter_for_vendors', default=u'Filter for vendors'),
                },
            )
        # customers of current user
        customers = customers_form_vocab()
        customer_selector = None
        # customers selection, include if more than one customer
        if len(customers) > 2:
            customer_selector = factory(
                'div:label:select',
                name='customer',
                value=self.request.form.get('customer', ''),
                props={
                    'vocabulary': customers,
                    'label': _('filter_for_customers', default=u'Filter for customers'),
                },
            )

        states = states_form_vocab()
        state_selector = factory(
            'div:label:select',
            name='state',
            value=self.request.form.get('state', ''),
            props={
                'vocabulary': states,
                'label': _('filter_for_state', default=u'Filter for states'),
            },
        )

        salaried = salaried_form_vocab()
        salaried_selector = factory(
            'div:label:select',
            name='salaried',
            value=self.request.form.get('salaried', ''),
            props={
                'vocabulary': salaried,
                'label': _('filter_for_salaried', default=u'Filter for salaried state'),
            },
        )

        # concatenate filters
        filter_widgets = ''
        if vendor_selector:
            filter_widgets += vendor_selector(request=self.request)
        if customer_selector:
            filter_widgets += customer_selector(request=self.request)

        filter_widgets += state_selector(request=self.request)
        filter_widgets += salaried_selector(request=self.request)

        return filter_widgets

    def render_order_actions_head(self):
        tag = Tag(Translate(self.request))
        select_all_orders_attrs = {
            'name': 'select_all_orders',
            'type': 'checkbox',
            'class_': 'select_all_orders',
            'title': _('select_all_orders', default=u'Select all visible orders'),
        }
        select_all_orders = tag('input', **select_all_orders_attrs)
        notify_customers_target = self.context.absolute_url()
        notify_customers_attributes = {
            'ajax:target': notify_customers_target,
            'class_': 'notify_customers',
            'href': '',
            'title': _(
                'notify_customers', default=u'Notify customers of selected orders'
            ),
        }
        notify_customers = tag('a', '&nbsp;', **notify_customers_attributes)
        return select_all_orders + notify_customers

    def render_order_actions(self, colname, record):
        tag = Tag(Translate(self.request))
        vendor_uid = self.request.form.get('vendor', '')
        base_url = self.context.absolute_url()

        # view order
        if vendor_uid:
            view_order_target = '%s?uid=%s&vendor=%s' % (
                base_url,
                str(record.attrs['uid']),
                vendor_uid,
            )
        else:
            view_order_target = '%s?uid=%s' % (base_url, str(record.attrs['uid']))
        view_order_attrs = {
            'ajax:bind': 'click',
            'ajax:target': view_order_target,
            'ajax:overlay': 'order',
            'href': '',
            'title': _('view_order', default=u'View Order'),
        }
        order_icon_url = '%s/++resource++bda.plone.orders/order.png' % base_url
        view_order_icon = tag('img', src=order_icon_url)
        view_order = tag('a', view_order_icon, **view_order_attrs)

        # view invoice
        view_invoice_target = '%s?uid=%s' % (base_url, str(record.attrs['uid']))
        view_invoice_attrs = {
            'ajax:bind': 'click',
            'ajax:target': view_invoice_target,
            'ajax:overlay': 'invoice',
            'ajax:overlay-css': 'invoice_overlay',
            'href': '',
            'title': _('view_invoice', default=u'View Invoice'),
        }
        invoice_icon_url = '%s/++resource++bda.plone.orders/invoice.png' % base_url
        view_invoice_icon = tag('img', src=invoice_icon_url)
        view_invoice = tag('a', view_invoice_icon, **view_invoice_attrs)

        # select order
        select_order_attrs = {
            'name': 'select_order',
            'type': 'checkbox',
            'value': record.attrs['uid'],
            'class_': 'select_order',
        }
        select_order = tag('input', **select_order_attrs)

        # return joined actions
        return select_order + view_order + view_invoice

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
            salaried = OrderData(self.context, order=record).salaried
            return translate(vocabs.salaried_vocab()[salaried], context=self.request)
        return OrderSalariedDropdown(self.context, self.request, record).render()

    def render_state(self, colname, record):
        if not self.check_modify_order(record):
            state = OrderData(self.context, order=record).state
            return translate(vocabs.state_vocab()[state], context=self.request)
        return OrderStateDropdown(self.context, self.request, record).render()

    @property
    def ajaxurl(self):
        params = [
            ('vendor', self.request.form.get('vendor')),
            ('customer', self.request.form.get('customer')),
            ('state', self.request.form.get('state')),
            ('salaried', self.request.form.get('salaried')),
        ]
        query = six.moves.urllib.parse.urlencode(dict([it for it in params if it[1]]))
        query = query and u'?{0}'.format(query) or ''
        return u'{0:s}/{1:s}{2:s}'.format(
            self.context.absolute_url(), self.data_view_name, query
        )

    def __call__(self):
        # check if authenticated user is vendor
        if not get_vendors_for():
            raise Unauthorized
        # disable diazo theming if ajax call
        if '_' in self.request.form:
            self.request.response.setHeader('X-Theme-Disabled', 'True')
        return super(OrdersTable, self).__call__()


class MyOrdersTable(OrdersTableBase):
    data_view_name = '@@myordersdata'

    def render_order_actions(self, colname, record):
        tag = Tag(Translate(self.request))
        base_url = self.context.absolute_url()

        # view order
        view_order_target = '%s?uid=%s' % (base_url, str(record.attrs['uid']))
        view_order_attrs = {
            'ajax:bind': 'click',
            'ajax:target': view_order_target,
            'ajax:overlay': 'myorder',
            'href': '',
            'title': _('view_order', default=u'View Order'),
        }
        order_icon_url = '%s/++resource++bda.plone.orders/order.png' % base_url
        view_order_icon = tag('img', src=order_icon_url)
        view_order = tag('a', view_order_icon, **view_order_attrs)

        # view invoice
        view_invoice_target = '%s?uid=%s' % (base_url, str(record.attrs['uid']))
        view_invoice_attrs = {
            'ajax:bind': 'click',
            'ajax:target': view_invoice_target,
            'ajax:overlay': 'myinvoice',
            'ajax:overlay-css': 'invoice_overlay',
            'href': '',
            'title': _('view_invoice', default=u'View Invoice'),
        }
        invoice_icon_url = '%s/++resource++bda.plone.orders/invoice.png' % base_url
        view_invoice_icon = tag('img', src=invoice_icon_url)
        view_invoice = tag('a', view_invoice_icon, **view_invoice_attrs)

        # return joined actions
        return view_order + view_invoice

    def __call__(self):
        # disable diazo theming if ajax call
        if '_' in self.request.form:
            self.request.response.setHeader('X-Theme-Disabled', 'True')
        return super(MyOrdersTable, self).__call__()


class OrdersData(OrdersTable, TableData):
    soup_name = 'bda_plone_orders_orders'
    search_text_index = 'text'

    def _get_buyables_in_context(self):
        catalog = plone.api.portal.get_tool("portal_catalog")
        path = '/'.join(self.context.getPhysicalPath())
        brains = catalog(path=path, object_provides=IBuyable.__identifier__)
        for brain in brains:
            yield brain.UID

    def query(self, soup):
        # fetch user vendor uids
        vendor_uids = get_vendor_uids_for()
        # filter by given vendor uid or user vendor uids
        vendor_uid = self.request.form.get('vendor')
        if vendor_uid:
            vendor_uid = uuid.UUID(vendor_uid)
            # raise if given vendor uid not in user vendor uids
            if vendor_uid not in vendor_uids:
                raise Unauthorized
            query = Any('vendor_uids', [vendor_uid])
        else:
            query = Any('vendor_uids', vendor_uids)

        # filter by customer if given
        customer = self.request.form.get('customer')
        if customer:
            query = query & Eq('creator', customer)

        # Filter by state if given
        state = self.request.form.get('state')
        if state:
            query = query & Eq('state', state)

        # Filter by salaried if given
        salaried = self.request.form.get('salaried')
        if salaried:
            query = query & Eq('salaried', salaried)

        # filter by search term if given
        term = self.request.form['sSearch']
        if six.PY2:
            term = term.decode('utf-8')
        if term:
            # append * for proper fulltext search
            term += '*'
            query = query & Contains(self.search_text_index, term)
        # get buyable uids for given context, get all buyables on site root
        # use explicit IPloneSiteRoot to make it play nice with lineage
        if not IPloneSiteRoot.providedBy(self.context):
            buyable_uids = self._get_buyables_in_context()
            query = query & Any('buyable_uids', buyable_uids)
        # query orders and return result
        sort = self.sort()
        res = soup.lazy(
            query, sort_index=sort['index'], reverse=sort['reverse'], with_size=True
        )
        length = next(res)
        return length, res


class MyOrdersData(MyOrdersTable, TableData):
    soup_name = 'bda_plone_orders_orders'
    search_text_index = 'text'

    def query(self, soup):
        query = Eq('creator', plone.api.user.get_current().getId())
        # filter by search term if given
        term = self.request.form['sSearch']
        if six.PY2:
            term = term.decode('utf-8')
        if term:
            # append * for proper fulltext search
            term += '*'
            query = query & Contains(self.search_text_index, term)
        # query orders and return result
        sort = self.sort()
        res = soup.lazy(
            query, sort_index=sort['index'], reverse=sort['reverse'], with_size=True
        )
        length = next(res)
        return length, res
