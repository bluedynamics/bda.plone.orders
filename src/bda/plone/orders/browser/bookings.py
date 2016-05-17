# -*- coding: utf-8 -*-
from bda.intellidatetime import convert
from bda.intellidatetime import DateTimeConversionError
from bda.plone.orders import interfaces as ifaces
from bda.plone.orders import message_factory as _
from bda.plone.orders import permissions
from bda.plone.orders import vocabularies as vocabs
from bda.plone.orders.browser.dropdown import BaseDropdown
from bda.plone.orders.common import BookingData
from bda.plone.orders.common import DT_FORMAT
from bda.plone.orders.common import get_bookings_soup
from bda.plone.orders.common import get_order
from bda.plone.orders.common import get_vendor_by_uid
from bda.plone.orders.common import get_vendor_uids_for
from bda.plone.orders.interfaces import IBuyable
from bda.plone.orders.transitions import transitions_of_main_state
from bda.plone.orders.transitions import transitions_of_salaried_state
from decimal import Decimal
from odict import odict
from Products.CMFPlone.utils import safe_unicode
from Products.Five import BrowserView
from repoze.catalog.query import Contains
from repoze.catalog.query import Ge
from repoze.catalog.query import InRange
from repoze.catalog.query import Le
from yafowil.base import factory
from zExceptions import InternalError
from zope.i18n import translate

import datetime
import json
import plone.api
import yafowil.loader  # noqa


class BookingsDropdown(BaseDropdown):

    @property
    def booking_data(self):
        vendor_uid = self.request.form.get('vendor', '')
        if vendor_uid:
            vendor_uids = [vendor_uid]
        else:
            vendor_uids = get_vendor_uids_for()

        return BookingData(
            self.context,
            booking=self.record,
            vendor_uids=vendor_uids
        )


class StateDropdown(BookingsDropdown):
    name = 'state'
    css = 'dropdown change_booking_state_dropdown'
    action = 'statetransition'
    subtype = 'booking'
    vocab = vocabs.state_vocab()
    transitions = vocabs.state_transitions_vocab()

    @property
    def value(self):
        return self.booking_data.booking.attrs['state']

    @property
    def items(self):
        transitions = transitions_of_main_state(self.value)
        return self.create_items(transitions)


class SalariedDropdown(BookingsDropdown):
    name = 'salaried'
    css = 'dropdown change_booking_salaried_dropdown'
    action = 'salariedtransition'
    subtype = 'booking'
    vocab = vocabs.salaried_vocab()
    transitions = vocabs.salaried_transitions_vocab()

    @property
    def value(self):
        return self.booking_data.booking.attrs['salaried'] \
               or ifaces.SALARIED_NO

    @property
    def items(self):
        transitions = transitions_of_salaried_state(self.value)
        return self.create_items(transitions)


class BookingsTable(BrowserView):
    table_id = 'bdaplonebookings'
    data_view_name = '@@bookingsdata'

    def render_group_filter(self):
        # group orders
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

    def render_date_from_filter(self):
        from_date = factory(
            'label:text',
            name='from_date',
            value=self.request.form.get('from_date', ''),
            props={
                'label': _('from_date',
                           default=u'Filter from date'),
            }
        )
        filter = from_date(request=self.request)
        return filter

    def render_date_to_filter(self):
        to_date = factory(
            'label:text',
            name='to_date',
            value=self.request.form.get('to_date', ''),
            props={
                'label': _('to_date',
                           default=u'to date'),
            }
        )
        filter = to_date(request=self.request)
        return filter

    def render_dt(self, colname, record):
        value = record.attrs.get(colname, '')
        if value:
            value = value.strftime(DT_FORMAT)
            return value

    def render_email(self, colname, record):
        email = record.attrs.get(colname, '')
        bookings_quantity = self.render_bookings_quantity(colname, record)
        bookings_total_sum = self.render_bookings_total_sum(colname, record)
        value = \
            '<tr class="group_email">' \
            '<td colspan="13">' + '<p>' + email + '</p>' +\
            '<span>' +\
            translate(
                _("bookings_quantity", default=u"Bookings quantity"),
                self.request
            ) \
            + ': ' + str(bookings_quantity) + '</span>' \
            '<span>' +\
            translate(
                _("bookings_total_sum", default=u"Bookings total sum"),
                self.request
            ) \
            + ': ' + str(bookings_total_sum) + '</td></tr>'

        return value

    def render_buyable_uid(self, colname, record):
        # this actually gets the title of a buyable_uid
        title = record.attrs.get('title', '')
        bookings_quantity = self.render_bookings_quantity(colname, record)
        bookings_total_sum = self.render_bookings_total_sum(colname, record)
        value = \
            u'<tr class="group_buyable">' \
            u'<td colspan="13">' + u'<p>' + safe_unicode(title) + u'</p>' +\
            u'<span>' +\
            translate(
                _("bookings_quantity", default=u"Bookings quantity"),
                self.request
            ) \
            + u': ' + safe_unicode(bookings_quantity) + u'</span>' \
            u'<span>' +\
            translate(
                _("bookings_total_sum", default=u"Bookings total sum"),
                self.request
            ) \
            + u': ' + bookings_total_sum + u'</td></tr>'

        return value

    def render_count(self, colname, record):
        value = record.attrs.get(colname, '')
        unit = record.attrs.get('quantity_unit', '')
        if value:
            value = Decimal(value)
            value = str(value) + ' ' + unit
            return value

    def render_price_per_unit(self, colname, record):
        currency = record.attrs.get('currency', '')
        price = self._get_price(record)
        if currency and price:
            value = currency + ' {0:.2f}'.format(price)
            return value

    def render_sum(self, colname, record):
        currency = record.attrs.get('currency', '')
        count = record.attrs.get('buyable_count', '')
        price = self._get_price(record)
        if currency and price and count:
            count = Decimal(count)
            sum = price * count
            value = currency + ' {0:.2f}'.format(sum)
            return value

    def render_bookings_quantity(self, colname, record):
        value = record._v_bookings_quantity
        if value:
            return str(value)

    def render_bookings_total_sum(self, colname, record):
        currency = record.attrs.get('currency', '')
        value = record._v_bookings_total_sum
        if currency and value:
            value = currency + ' {0:.2f}'.format(value)
            return value

    @property
    def ajaxurl(self):
        return '%s/%s' % (self.context.absolute_url(), self.data_view_name)

    @property
    def columns(self):
        columns = [
            {
                'id': 'email',
                'label': _('email', default=u'Email'),
                'renderer': self.render_email,
                'origin': 'b',
            },
            {
                'id': 'buyable_uid',
                'label': _('buyable_uid', default=u'Buyable Uid'),
                'renderer': self.render_buyable_uid,
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
            {
                'id': 'personal_data.phone',
                'label': _('phone', default=u'Phone'),
                'origin': 'o',
            },
            {
                'id': 'price_per_unit',
                'label': _('price_per_unit', default=u'Price per unit'),
                'renderer': self.render_price_per_unit,
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
            },
            {
                'id': 'booking_quantity',
                'label': _('bookings_quantity', default=u'Bookings quantity'),
                'renderer': self.render_bookings_quantity,
                'origin': 'b',
            },
            {
                'id': 'bookings_total_sum',
                'label': _(
                    'bookings_total_sum',
                    default=u'Bookings total sum'
                ),
                'renderer': self.render_bookings_total_sum,
                'origin': 'b',
            },
            {
                'id': 'salaried',
                'label': _('salaried', default=u'Salaried'),
                'renderer': self.render_salaried,
                'origin': 'b',
            },
            {
                'id': 'state',
                'label': _('state', default=u'State'),
                'renderer': self.render_state,
                'origin': 'b',
            },
        ]
        return columns

    def jsondata(self):
        soup = get_bookings_soup(self.context)
        aaData = list()
        size, result = self.query(soup)

        columns = self.columns
        colnames = [_['id'] for _ in columns]

        def record2list(record, bookings_quantity=None):
            result = list()
            for colname in colnames:
                coldef = self.column_def(colname)
                renderer = coldef.get('renderer')

                if coldef['origin'] == 'o':
                    if renderer:
                        value = renderer(colname, record)
                    else:
                        value = self._get_ordervalue(colname, record)
                else:
                    if renderer:
                        value = renderer(colname, record)
                    else:
                        value = record.attrs.get(colname, '')

                result.append(value)
            return result

        for key in result:
            bookings_quantity = 0
            bookings_total_sum = 0
            for record in result[key]:
                bookings_quantity += record.attrs.get('buyable_count') or 0
                bookings_total_sum += self._get_sum(record)
            for record in result[key]:
                record._v_bookings_quantity = bookings_quantity
                record._v_bookings_total_sum = bookings_total_sum
                aaData.append(record2list(record))

        data = {
            "draw": int(self.request.form['draw']),
            "recordsTotal": size,
            "recordsFiltered": size,
            "data": aaData,
        }

        self.request.response.setHeader(
            'Content-Type',
            'application/json; charset=utf-8'
        )
        return json.dumps(data)

# helper methods
    def _get_price(self, record):
        """
        returns net + vat price
        """
        net = record.attrs.get('net', '')
        vat_percent = record.attrs.get('vat', '')
        if net and vat_percent:
            net = Decimal(net)
            vat_percent = Decimal(vat_percent)
            vat = 1 + vat_percent / 100
            return net * vat
        return net and Decimal(net) or Decimal(0)

    def _get_sum(self, record):
        """
        returns net + vat * count
        """
        count = record.attrs.get('buyable_count', '')
        price = self._get_price(record)
        if price and count:
            count = Decimal(count)
            sum = price * count
            return Decimal(sum)
        return Decimal(0)

    def _get_ordervalue(self, colname, record):
        """
        helper method to get the values which are saved on the order and not
        on the booking itself.
        """
        order = get_order(self.context, record.attrs.get('order_uid'))
        value = order.attrs.get(colname, '')
        return value

    def slice(self, fullresult):
        start = int(self.request.form['start'])
        length = int(self.request.form['length'])
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

    def _datetime_checker(self, from_date, to_date):
        # get portal language for datetime locale formating
        # used for quering
        portal = plone.api.portal.get()
        locale = portal.language
        if len(from_date) > 0:
            try:
                from_date = convert(from_date, locale=locale)
            except DateTimeConversionError:
                return None
        if len(to_date) > 0:
            try:
                to_date = convert(to_date, locale=locale)
            except DateTimeConversionError:
                return None
            if isinstance(to_date, datetime.datetime) \
                    and to_date.hour == 0 and to_date.minute == 0:
                to_date = to_date.replace(hour=23, minute=59, second=59)

        if isinstance(from_date, str) and isinstance(to_date, str):
            return None
        if isinstance(from_date, datetime.datetime) \
                and isinstance(to_date, str):
            return Ge('created', from_date)
        if isinstance(from_date, str) \
                and isinstance(to_date, datetime.datetime):
            return Le('created', to_date)
        if isinstance(from_date, datetime.datetime) \
                and isinstance(to_date, datetime.datetime):
            return InRange('created', from_date, to_date)

    def _text_checker(self, text):
        # used for quering
        if len(text) < 1:
            return None
        return Contains('text', text + '*')

    def _get_buyables_in_context(self):
        catalog = plone.api.portal.get_tool("portal_catalog")
        path = '/'.join(self.context.getPhysicalPath())
        brains = catalog(path=path, object_provides=IBuyable.__identifier__)
        for brain in brains:
            yield brain.UID

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

    def query(self, soup):
        self._get_buyables_in_context()
        req_group_id = self.request.get('group_by', 'email')
        # if no req group is set
        if len(req_group_id) == 0:
            req_group_id = 'email'

        if req_group_id not in vocabs.groups_vocab():
            raise InternalError('Group not allowed!')
        # not pretty but, otherwise there a problems with vocab + soup attrs
        # that need many places to refactor to make it work
        if req_group_id == 'buyable':
            req_group_id = 'buyable_uid'

        group_index = soup.catalog[req_group_id]

        booking_uids = soup.catalog['uid']
        req_from_date = self.request.get('from_date', '')
        req_to_date = self.request.get('to_date', '')
        req_text = self.request.get('search[value]', '')

        date_query = self._datetime_checker(req_from_date, req_to_date)
        text_query = self._text_checker(req_text)

        if date_query and not text_query:
            dummysize, bookings_set = soup.catalog.query(date_query)
        elif text_query and not date_query:
            dummysize, bookings_set = soup.catalog.query(text_query)
        elif date_query and text_query:
            query = date_query & text_query
            dummysize, bookings_set = soup.catalog.query(query)
        else:
            bookings_set = booking_uids._rev_index.keys()
        bookings_set = set(bookings_set)

        buyable_index = soup.catalog['buyable_uid']
        buyables_set = set()
        # get all buyables for the current context/path
        for buyable_uid in self._get_buyables_in_context():
            try:
                buyables_set.update(buyable_index._fwd_index[buyable_uid])
            except KeyError:
                continue
        # filter bookings_set to only match the current context/path
        bookings_set = bookings_set.intersection(buyables_set)

        unique_group_ids = []
        # for each booking which matches the query append the qroup id once
        for group_id, group_booking_ids in group_index._fwd_index.items():
            if bookings_set.intersection(group_booking_ids):
                unique_group_ids.append(group_id)

        res = odict()
        size = len(unique_group_ids)

        # for each unique group id  get the matching group booking ids
        for group_id in self.slice(unique_group_ids):
            res[group_id] = []
            for group_booking_id in group_index._fwd_index[group_id]:
                if group_booking_id in bookings_set:
                    res[group_id].append(soup.get(group_booking_id))

        return size, res

    def render_salaried(self, colname, record):
        if not self.check_modify_order(record):
            salaried = BookingData(
                self.context,
                booking=record
            ).booking.salaried
            return translate(
                vocabs.salaried_vocab()[salaried],
                context=self.request
            )
        return SalariedDropdown(self.context, self.request, record).render()

    def render_state(self, colname, record):
        if not self.check_modify_order(record):
            state = BookingData(
                self.context,
                booking=record
            ).booking.state
            return translate(
                vocabs.state_vocab()[state],
                context=self.request
            )
        return StateDropdown(self.context, self.request, record).render()
