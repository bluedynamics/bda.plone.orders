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
from bda.plone.checkout import (
    CheckoutAdapter,
    CheckoutError,
)
from bda.plone.cart import (
    readcookie,
    extractitems,
    get_data_provider,
    get_item_data_provider,
    get_item_stock,
    get_item_state,
    get_catalog_brain,
    get_object_by_uid,
)
from bda.plone.shipping import Shippings
from bda.plone.payment.six_payment import ISixPaymentData


DT_FORMAT = '%d.%m.%Y %H:%M'


def create_ordernumber():
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
        ordernumber_indexer = NodeAttributeIndexer('ordernumber')
        catalog[u'ordernumber'] = CatalogFieldIndex(ordernumber_indexer)
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
        firstname_indexer = NodeAttributeIndexer('personal_data.firstname')
        catalog[u'personal_data.firstname'] = CatalogFieldIndex(firstname_indexer)
        lastname_indexer = NodeAttributeIndexer('personal_data.lastname')
        catalog[u'personal_data.lastname'] = CatalogFieldIndex(lastname_indexer)
        city_indexer = NodeAttributeIndexer('billing_address.city')
        catalog[u'billing_address.city'] = CatalogFieldIndex(city_indexer)
        search_attributes = ['personal_data.lastname',
                             'personal_data.firstname',
                             'billing_address.city',
                             'ordernumber']
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

    @property
    def items(self):
        return extractitems(readcookie(self.request))

    def ordernumber_exists(self, soup, ordernumber):
        for order in soup.query(Eq('ordernumber', ordernumber)):
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
        sid = data.fetch('checkout.shipping_selection.shipping').extracted
        shipping = Shippings(self.context).get(sid)
        order.attrs['shipping'] = shipping.calculate(self.items)
        uid = order.attrs['uid'] = uuid.uuid4()
        order.attrs['creator'] = creator
        order.attrs['created'] = created
        order.attrs['state'] = 'new'
        order.attrs['salaried'] = 'no'
        bookings = self.create_bookings(order)
        order.attrs['booking_uids'] = [_.attrs['uid'] for _ in bookings]
        orders_soup = get_soup('bda_plone_orders_orders', self.context)
        ordernumber = create_ordernumber()
        while self.ordernumber_exists(orders_soup, ordernumber):
            ordernumber = create_ordernumber()
        order.attrs['ordernumber'] = ordernumber
        orders_soup.add(order)
        bookings_soup = get_soup('bda_plone_orders_bookings', self.context)
        for booking in bookings:
            bookings_soup.add(booking)
        return uid

    def create_bookings(self, order):
        ret = list()
        cart_data = get_data_provider(self.context)
        currency = cart_data.currency
        items = self.items
        for uid, count, comment in items:
            brain = get_catalog_brain(self.context, uid)
            obj = brain.getObject()
            item_state = get_item_state(obj, self.request)
            if not item_state.validate_count(item_state.aggregated_count):
                raise CheckoutError(u'Item no longer available')
            item_stock = get_item_stock(obj)
            item_stock.available -= float(count)
            item_data = get_item_data_provider(obj)
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
    def shipping(self):
        return float(self.order.attrs['shipping'])

    @property
    def total(self):
        ret = 0.0
        for booking in self.bookings:
            count = float(booking.attrs['buyable_count'])
            net = booking.attrs.get('net', 0.0) * count
            ret += net
            ret += net * booking.attrs.get('vat', 0.0) / 100
        return ret + self.shipping

    def increase_stock(self, bookings):
        for booking in bookings:
            obj = get_object_by_uid(self.context, booking.attrs['buyable_uid'])
            # object no longer exists
            if not obj:
                continue
            stock = get_item_stock(obj)
            stock.available += float(booking.attrs['buyable_count'])

    def decrease_stock(self, bookings):
        for booking in bookings:
            obj = get_object_by_uid(self.context, booking.attrs['buyable_uid'])
            # object no longer exists
            if not obj:
                continue
            stock = get_item_stock(obj)
            stock.available -= float(booking.attrs['buyable_count'])


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
            attrs['personal_data.firstname'],
            attrs['personal_data.lastname'],
            attrs['billing_address.city'],
            amount])
        return description

    @property
    def ordernumber(self):
        return self.order_data.order.attrs['ordernumber']

    def uid_for(self, ordernumber):
        soup = get_soup('bda_plone_orders_orders', self.context)
        for order in soup.query(Eq('ordernumber', ordernumber)):
            return str(order.attrs['uid'])

    def data(self, order_uid):
        self.order_uid = order_uid
        return {
            'amount': self.amount,
            'currency': self.currency,
            'description': self.description,
            'ordernumber': self.ordernumber,
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
        order_data = OrderData(self.context, uid)
        order = order_data.order
        if transition == 'mark_salaried':
            order.attrs['salaried'] = 'yes'
        elif transition == 'mark_outstanding':
            order.attrs['salaried'] = 'no'
        elif transition == 'renew':
            order.attrs['state'] = 'new'
            order_data.decrease_stock(order_data.bookings)
        elif transition == 'finish':
            order.attrs['state'] = 'finished'
        elif transition == 'cancel':
            order.attrs['state'] = 'cancelled'
            order_data.increase_stock(order_data.bookings)
        else:
            raise ValueError(u"invalid transition: %s" % transition)
        soup = get_soup('bda_plone_orders_orders', self.context)
        soup.reindex(records=[order])
        return order
