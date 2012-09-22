import uuid
import time
import datetime
from zope.interface import implementer
from repoze.catalog.catalog import Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.keyword import CatalogKeywordIndex
from repoze.catalog.indexes.text import CatalogTextIndex
from repoze.catalog.query import Eq
from souper.interfaces import ICatalogFactory
from souper.soup import (
    get_soup,
    Record,
    NodeAttributeIndexer,
    NodeTextIndexer,
)
from node.utils import instance_property
from node.ext.zodb import OOBTNode
from bda.plone.checkout import CheckoutAdapter
from bda.plone.cart import (
    readcookie,
    extractitems,
    get_catalog_brain,
)
from bda.plone.cart import (
    get_data_provider,
    get_item_data_provider,
)
from bda.plone.payment.six_payment import ISixPaymentData


DT_FORMAT = '%m.%d.%Y %H:%M'


def ordernumber():
    onum = hash(time.time())
    if onum < 0:
        return '0%s' % str(abs(onum))
    return '1%s' % str(onum)


def get_order(context, uid):
    if not isinstance(uid, uuid.UUID):
        uid = uuid.UUID(uid)
    soup = get_soup('bda_plone_orders_orders', context)
    return [_ for _ in soup.query(Eq('uid', uid))][0]


@implementer(ICatalogFactory)
class BookingsCatalogFactory(object):

    def __call__(self, context=None):
        catalog = Catalog()
        uid_indexer = NodeAttributeIndexer('uid')
        catalog[u'uid'] = CatalogFieldIndex(uid_indexer)
        buyable_uid_indexer = NodeAttributeIndexer('buyable_uid')
        catalog[u'buyable_uid'] = CatalogFieldIndex(buyable_uid_indexer)
        order_uid_indexer = NodeAttributeIndexer('order_uid')
        catalog[u'order_uid'] = CatalogFieldIndex(order_uid_indexer)
        creator_indexer = NodeAttributeIndexer('creator')
        catalog[u'creator'] = CatalogFieldIndex(creator_indexer)
        created_indexer = NodeAttributeIndexer('created')
        catalog[u'created'] = CatalogFieldIndex(created_indexer)
        exported_indexer = NodeAttributeIndexer('exported')
        catalog[u'exported'] = CatalogFieldIndex(exported_indexer)
        title_indexer = NodeAttributeIndexer('title')
        catalog[u'title'] = CatalogFieldIndex(title_indexer)
        return catalog


@implementer(ICatalogFactory)
class OrdersCatalogFactory(object):

    def __call__(self, context=None):
        catalog = Catalog()
        uid_indexer = NodeAttributeIndexer('uid')
        catalog[u'uid'] = CatalogFieldIndex(uid_indexer)
        orderid_indexer = NodeAttributeIndexer('orderid')
        catalog[u'orderid'] = CatalogFieldIndex(orderid_indexer)
        booking_uids_indexer = NodeAttributeIndexer('booking_uids')
        catalog[u'booking_uids'] = CatalogKeywordIndex(booking_uids_indexer)
        creator_indexer = NodeAttributeIndexer('creator')
        catalog[u'creator'] = CatalogFieldIndex(creator_indexer)
        created_indexer = NodeAttributeIndexer('created')
        catalog[u'created'] = CatalogFieldIndex(created_indexer)
        state_indexer = NodeAttributeIndexer('state')
        catalog[u'state'] = CatalogFieldIndex(state_indexer)
        salaried_indexer = NodeAttributeIndexer('salaried')
        catalog[u'salaried'] = CatalogFieldIndex(salaried_indexer)
        name_indexer = NodeAttributeIndexer('personal_data.name')
        catalog[u'personal_data.name'] = CatalogFieldIndex(name_indexer)
        surname_indexer = NodeAttributeIndexer('personal_data.surname')
        catalog[u'personal_data.surname'] = CatalogFieldIndex(surname_indexer)
        city_indexer = NodeAttributeIndexer('billing_address.city')
        catalog[u'billing_address.city'] = CatalogFieldIndex(city_indexer)
        search_attributes = ['personal_data.name',
                             'personal_data.surname',
                             'billing_address.city']
        text_indexer = NodeTextIndexer(search_attributes)
        catalog[u'text'] = CatalogTextIndex(text_indexer)
        return catalog


class OrderCheckoutAdapter(CheckoutAdapter):
    
    @instance_property
    def order(self):
        return OOBTNode()
    
    @property
    def vessel(self):
        return self.order.attrs
    
    def orderid_exists(self, soup, orderid):
        for order in soup.query(Eq('orderid', orderid)):
            return bool(order)
        return False
    
    def save(self, providers, widget, data):
        super(OrderCheckoutAdapter, self).save(providers, widget, data)
        creator = None
        member = self.context.portal_membership.getAuthenticatedMember()
        if member:
            creator = member.getId()
        created = datetime.datetime.now()
        order = self.order
        uid = order.attrs['uid'] = uuid.uuid4()
        order.attrs['creator'] = creator
        order.attrs['created'] = created
        order.attrs['state'] = 'new'
        order.attrs['salaried'] = 'no'
        bookings = self.create_bookings(order)
        order.attrs['booking_uids'] = [_.attrs['uid'] for _ in bookings]
        orders_soup = get_soup('bda_plone_orders_orders', self.context)
        orderid = ordernumber()
        while self.orderid_exists(orders_soup, orderid):
            orderid = ordernumber()
        order.attrs['orderid'] = orderid
        orders_soup.add(order)
        bookings_soup = get_soup('bda_plone_orders_bookings', self.context)
        for booking in bookings:
            bookings_soup.add(booking)
        return uid
    
    def create_bookings(self, order):
        ret = list()
        currency = get_data_provider(self.context).currency
        items = extractitems(readcookie(self.request))
        for uid, count, comment in items:
            brain = get_catalog_brain(self.context, uid)
            item_data = get_item_data_provider(brain.getObject())
            booking = OOBTNode()
            booking.attrs['uid'] = uuid.uuid4()
            booking.attrs['buyable_uid'] = uid
            booking.attrs['buyable_count'] = count
            booking.attrs['buyable_comment'] = comment
            booking.attrs['order_uid'] = order.attrs['uid']
            booking.attrs['creator'] = order.attrs['creator']
            booking.attrs['created'] = order.attrs['created']
            booking.attrs['exported'] = False
            booking.attrs['title'] = brain and brain.Title or 'unknown'
            booking.attrs['net'] = item_data.net
            booking.attrs['vat'] = item_data.vat
            booking.attrs['currency'] = currency
            booking.attrs['quantity_unit'] = item_data.quantity_unit
            ret.append(booking)
        return ret


class OrderData(object):
    
    def __init__(self, context, uid):
        self.context = context
        if not isinstance(uid, uuid.UUID):
            uid = uuid.UUID(uid)
        self.uid = uid
    
    @property
    def order(self):
        return get_order(self.context, self.uid)
    
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
        return ret
    
    @property
    def vat(self):
        ret = 0.0
        for booking in self.bookings:
            count = float(booking.attrs['buyable_count'])
            net = booking.attrs.get('net', 0.0) * count
            ret += net * booking.attrs.get('vat', 0.0) / 100
        return ret
    
    @property
    def total(self):
        ret = 0.0
        for booking in self.bookings:
            count = float(booking.attrs['buyable_count'])
            net = booking.attrs.get('net', 0.0) * count
            ret += net
            ret += net * booking.attrs.get('vat', 0.0) / 100
        return ret


@implementer(ISixPaymentData)
class SixPaymentData(object):
    
    def __init__(self, context):
        self.context = context
    
    @instance_property
    def order_data(self):
        return OrderData(self.context, self.order_uid)
    
    @property
    def amount(self):
        amount = '%0.2f' % self.order_data.total
        amount = amount[:amount.index('.')] + amount[amount.index('.') + 1:]
        return amount
    
    @property
    def currency(self):
        return get_data_provider(self.context).currency
    
    @property
    def description(self):
        order = self.order_data.order
        attrs = order.attrs
        amount = '%s %s' % (self.currency, str(round(self.order_data.total, 2)))
        description = ', '.join([
            attrs['created'].strftime(DT_FORMAT),
            attrs['personal_data.name'],
            attrs['personal_data.surname'],
            attrs['billing_address.city'],
            amount])
        return description
    
    def data(self, order_uid):
        self.order_uid = order_uid
        return {
            'amount': self.amount,
            'currency': self.currency,
            'description': self.description,
        }


def payment_success(event):
    if event.payment.pid == 'six_payment':
        data = event.data
        order = get_order(event.context, event.order_uid)
        order.attrs['salaried'] = 'yes'
        order.attrs['tid'] = data['tid']


def payment_failed(event):
    if event.payment.pid == 'six_payment':
        data = event.data
        order = get_order(event.context, event.order_uid)
        order.attrs['salaried'] = 'failed'
        order.attrs['tid'] = data['tid']


class OrderTransitions(object):
    
    def __init__(self, context):
        self.context = context
    
    def do_transition(self, uid, transition):
        """Do transition for order by UID and transition name.
        
        @param uid: uuid.UUID or string representing a UUID
        @param transition: string
        
        @return: order record
        """
        if not isinstance(uid, uuid.UUID):
            uid = uuid.UUID(uid)
        record = get_order(self.context, uid)
        if transition == 'mark_salaried':
            record.attrs['salaried'] = 'yes'
        elif transition == 'mark_outstanding':
            record.attrs['salaried'] = 'no'
        elif transition == 'renew':
            record.attrs['state'] = 'new'
        elif transition == 'finish':
            record.attrs['state'] = 'finished'
        elif transition == 'cancel':
            record.attrs['state'] = 'cancelled'
        else:
            raise ValueError(u"invalid transition: %s" % transition)
        soup = get_soup('bda_plone_orders_orders', self.context)
        soup.reindex(records=[record])
        return record
