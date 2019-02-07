# -*- coding: utf-8 -*-
from Products.CMFPlone.utils import safe_unicode
from bda.plone.orders import message_factory as _
from bda.plone.orders.browser.common import ContentViewBase
from bda.plone.orders.browser.common import Translate
from bda.plone.orders.contacts import get_contacts_soup
from repoze.catalog.query import Contains
from repoze.catalog.query import Gt
from yafowil.utils import Tag
from zope.i18n import translate
from zope.i18nmessageid import Message
import json
import plone.api
import yafowil.loader  # noqa
import uuid

FLOORUID = uuid.UUID(31*'0'+'1')


class ContactsTable(ContentViewBase):
    table_id = 'bdaplonecontacts'
    data_view_name = '@@contactsdata'

    def render_get_actions_for_contact(self, colname, record):
        tag = Tag(Translate(self.request))
        site = plone.api.portal.get()
        base_url = site.absolute_url()

        # view orders
        view_orders_target = '%s/@@orders#%s' % (
            base_url,
            str(record.attrs['personal_data.email']))
        view_orders_attrs = {
            'href': view_orders_target,
            'title': _('view_orders', default=u'View Orders'),
        }
        orders_icon_url = '%s/++resource++bda.plone.orders/orders.png' % base_url
        view_orders_icon = tag('img', src=orders_icon_url)
        view_orders = tag('a', view_orders_icon, **view_orders_attrs)

        # view bookings
        view_bookings_target = '%s/@@bookings#%s' % (
            base_url,
            str(record.attrs['personal_data.email']))
        view_bookings_attrs = {
            'href': view_bookings_target,
            'title': _('view_bookings', default=u'View Bookings'),
        }
        bookings_icon_url = '%s/++resource++bda.plone.orders/bookings.png' % base_url
        view_bookings_icon = tag('img', src=bookings_icon_url)
        view_bookings = tag('a', view_bookings_icon, **view_bookings_attrs)

        # XXX: view invoices

        return view_orders + view_bookings

    @property
    def ajaxurl(self):
        return '%s/%s' % (self.context.absolute_url(), self.data_view_name)

    @property
    def columns(self):
        return [
            {
                'id': 'actions',
                'label': _('actions', default=u'Actions'),
                'renderer': self.render_get_actions_for_contact,
            },
            {
                'id': 'personal_data.email',
                'label': _('email', default=u'Email'),
            },
            {
                'id': 'personal_data.lastname',
                'label': _('lastname', default=u'Last Name'),
            },
            {
                'id': 'personal_data.firstname',
                'label': _('firstname', default=u'First Name'),
            },
        ]

    def jsondata(self):
        # json response header needed?
        soup = get_contacts_soup(self.context)
        aaData = list()
        size, result = self.query(soup)

        columns = self.columns
        colnames = [_['id'] for _ in columns]

        def record2list(record, bookings_quantity=None):
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

        for lazyrecord in self.slice(result):
            aaData.append(record2list(lazyrecord()))

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

    def _text_checker(self, text):
        # used for query
        if len(text) < 1:
            return None
        return Contains('text', text + '*')

    def query(self, soup):
        # always get all contacts
        query = Gt('uid', FLOORUID)
        req_text = safe_unicode(self.request.get('search[value]', ''))
        text_query = self._text_checker(req_text)
        # take fulltext search into account
        if text_query:
            query = query & text_query

        res = soup.lazy(query, with_size=True)
        size = next(res)
        return size, res
