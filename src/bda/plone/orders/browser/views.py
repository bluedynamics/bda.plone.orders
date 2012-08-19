import json
import datetime
from zope.i18nmessageid import MessageFactory
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from repoze.catalog.query import Contains
from souper.soup import (
    get_soup,
    LazyRecord,
)
from ..common import DT_FORMAT

_ = MessageFactory('bda.plone.orders')


class TableData(BrowserView):
    soup_name = None
    search_text_index = None
    
    @property
    def columns(self):
        """Return list of dicts with column definitions:
        
        [{
            'id': 'colid',
            'label': 'Col Label',
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
    
    def __call__(self):
        soup = get_soup(self.soup_name, self.context)
        aaData = list()
        length, lazydata = self.query(soup)
        colnames = [_['id'] for _ in self.columns]
        def record2list(record):
            result = list()
            for colname in colnames:
                value = record.attrs.get(colname, '')
                if isinstance(value, datetime.datetime):
                    value = value.strftime(DT_FORMAT)
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
            'id': 'personal_data.surname',
            'label': _('surname', 'Surname'),
        }, {
            'id': 'personal_data.name',
            'label': _('name', 'Name'),
        }, {
            'id': 'billing_address.city',
            'label': _('city', 'City'),
        }, {
            'id': 'created',
            'label': _('date', 'Date'),
        }, {
            'id': 'state',
            'label': _('state', 'State'),
        }]


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