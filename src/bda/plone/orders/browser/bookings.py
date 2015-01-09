# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from bda.plone.cart import ascur
from bda.plone.cart import get_item_stock
from bda.plone.cart import get_object_by_uid
from bda.plone.checkout import message_factory as _co
from bda.plone.checkout.vocabularies import get_pycountry_name
from bda.plone.orders import interfaces as ifaces
from bda.plone.orders import message_factory as _
from bda.plone.orders import permissions
from bda.plone.orders import safe_encode
from bda.plone.orders import vocabularies as vocabs
from bda.plone.orders.common import DT_FORMAT
from bda.plone.orders.common import get_bookings_soup
from bda.plone.orders.common import get_order
from bda.plone.orders.common import get_orders_soup
from bda.plone.orders.common import get_vendor_by_uid
from bda.plone.orders.common import get_vendor_uids_for
from bda.plone.orders.common import get_vendors_for
from bda.plone.orders.common import OrderData
from bda.plone.orders.common import OrderTransitions
from bda.plone.orders.interfaces import IBuyable
from decimal import Decimal
from odict import odict
from plone.memoize import view
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.utils import getToolByName
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from repoze.catalog.query import Any
from repoze.catalog.query import Contains
from repoze.catalog.query import DoesNotContain
from repoze.catalog.query import Eq
from repoze.catalog.query import Ge
from repoze.catalog.query import Le
from souper.soup import get_soup
from souper.soup import LazyRecord
from StringIO import StringIO
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
import yafowil.loader  # loads registry  # nopep8


from bda.plone.orders.browser.views import Translate
from bda.plone.orders.browser.views import vendors_form_vocab
from bda.plone.orders.browser.views import customers_form_vocab


class BookingsTable(BrowserView):
    table_id = 'bdaplonebookings'
    data_view_name = '@@bookingsdata'

    def render_filter(self):
        #group orders
        groups = vocabs.groups_vocab()
        group_selector = factory(
            'label:select',
            name='group',
            value=self.request.form.get('group', ''),
            props={
                'vocabulary': groups,
                'label': _('group_orders_by',
                           default=u'Group orders by'),
            }
        )
        filter = group_selector(request=self.request)
        return filter

    def render_dt(self, colname, record):
        value = record.attrs.get(colname, '')
        if value:
            value = value.strftime(DT_FORMAT)
        return value

    def render_count(self, colname, record):
        value = record.attrs.get(colname, '')
        unit = record.attrs.get('quantity_unit', '')
        if value:
            value = str(value) + ' ' + unit
        return value

    def render_net(self, colname, record):
        value = record.attrs.get(colname, '')
        currency = record.attrs.get('currency', '')
        if value:
            value = currency + ' {0:.2f}'.format(value)
        return value

    def render_sum(self, colname, record):
        currency = record.attrs.get('currency', '')
        net = record.attrs.get('net', '')
        count = record.attrs.get('buyable_count', '')
        count = float(count)
        sum = net * count
        value = currency + ' {0:.2f}'.format(sum)
        return value

    @property
    def ajaxurl(self):
        site = plone.api.portal.get()
        return '%s/%s' % (site.absolute_url(), self.data_view_name)

    @property
    def columns(self):
        # note sind auf der fertigen order drauf aber niucht alle
        # self.order.attrs.keys()
        # ['personal_data.heading', 'personal_data.gender', 'personal_data.firstname',
        #  'personal_data.lastname', 'personal_data.email', 'personal_data.phone',
        #  'personal_data.company', 'billing_address.heading', 'billing_address.street',
        #  'billing_address.zip', 'billing_address.city', 'billing_address.country',
        #  'delivery_address.heading', 'delivery_address.alternative_delivery',
        #  'delivery_address.firstname', 'delivery_address.lastname', 'delivery_address.company',
        #  'delivery_address.street', 'delivery_address.zip', 'delivery_address.city',
        #  'delivery_address.country', 'shipping_selection.heading', 'shipping_selection.shipping',
        #  'payment_selection.heading', 'payment_selection.payment', 'order_comment.heading', 'order_comment.comment']

        return [
            # {
            #     'id': 'personal_data.email',
            #     'label': _('email', default=u'Email'),
            #     'origin': 'o',
            # },
            { # todo trotz index iwia nit sortable und soup rebuild added se a nit
              # bei ana nein order stehts dann aber brav drauf? info: in commonpy order email anschaun
                'id': 'email',
                'label': _('email', default=u'Email'),
                'origin': 'b',
            },
            { #needed for clustering, later wont be displayed in table
                'id': 'buyable_uid',
                'label': _('buyable_uid', default=u'Buyable Uid'),
                'origin': 'b',
            },
            {
                'id': 'ordernumber',
                'label': _('ordernumber', default=u'Ordernumber'),
                'origin': 'o',
            },
            {
                'id': 'created',
                'label': _('booking_date', default=u'Bookingdate'),
                'renderer': self.render_dt,
                'origin': 'b',
            },
            {
                'id': 'title',
                'label': _('Item', default=u'Item'),
                'origin': 'b',
            },
            {
                'id': 'personal_data.lastname',
                'label': _('lastname', default=u'Last Name'),
                'origin': 'o',
            },
            {
                'id': 'personal_data.firstname',
                'label': _('firstname', default=u'First Name'),
                'origin': 'o',
            },
            {
                'id': 'billing_address.street',
                'label': _('street', default=u'Street'),
                'origin': 'o',
            },
            {
                'id': 'billing_address.city',
                'label': _('city', default=u'City'),
                'origin': 'o',
            },
            # {
            #     #todo spater im event?
            #     'id':'attendee',
            #     'label': _('attendee', default=u'Attendee'),
            # },
            {  # todo is net ok oder net+vat?
                'id': 'net',
                'label': _('price_per_unit', default=u'Price per unit'),
                'renderer': self.render_net,
                'origin': 'b',
            },
            {
                'id': 'buyable_count',
                'label': _('count', default=u'Count'),
                'renderer': self.render_count,
                'origin': 'b',
            },
            {
                'id': 'sum',
                'label': _('sum', default=u'Sum'),
                'renderer': self.render_sum,
                'origin': 'b',
            }
        ]

    def _get_ordervalue(self, colname, record):
        """
        helper method to get the values which are saved on the order and not
        on the booking itself.
        """
        order = get_order(self.context, record.attrs.get('order_uid'))
        value = order.attrs.get(colname, '')
        return value

    def jsondata(self):
        soup = get_bookings_soup(self.context)
        aaData = list()
        length, lazydata = self.query(soup)
        columns = self.columns
        colnames = [_['id'] for _ in columns]
        # todo json response header einbaun, da no table einbaun einzelne hidden column. siehe js und html im bsp

        def record2list(record):
            result = list()
            for colname in colnames:
                coldef = self.column_def(colname)
                renderer = coldef.get('renderer')

                if coldef['origin'] == 'o':
                    value = self._get_ordervalue(colname, record)
                else:
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



# helpers
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

    def query(self, soup):
        # todo buildme =)
        now = datetime.datetime.now()
        query = Le('created', now)
        sort = self.sort()
        res = soup.lazy(query,
                        sort_index=sort['index'],
                        reverse=sort['reverse'],
                        with_size=True)
        length = res.next()
        return length, res
