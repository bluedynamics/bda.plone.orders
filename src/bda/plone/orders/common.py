from Acquisition import aq_parent
from Acquisition import aq_inner
from Products.CMFPlone.interfaces import IPloneSiteRoot
from bda.plone.cart import extractitems
from bda.plone.cart import get_catalog_brain
from bda.plone.cart import get_data_provider
from bda.plone.cart import get_item_data_provider
from bda.plone.cart import get_item_state
from bda.plone.cart import get_item_stock
from bda.plone.cart import get_object_by_uid
from bda.plone.cart import readcookie
from bda.plone.checkout import CheckoutAdapter
from bda.plone.checkout import CheckoutError
from bda.plone.orders import permissions
from bda.plone.orders.interfaces import IVendor
from bda.plone.payment.interfaces import IPaymentData
from bda.plone.shipping import Shippings
from bda.plone.shop.interfaces import IBuyable
from decimal import Decimal
from node.ext.zodb import OOBTNode
from node.utils import instance_property
from plone.uuid.interfaces import IUUID
from repoze.catalog.catalog import Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.keyword import CatalogKeywordIndex
from repoze.catalog.indexes.text import CatalogTextIndex
from repoze.catalog.query import Any
from repoze.catalog.query import Eq
from souper.interfaces import ICatalogFactory
from souper.soup import NodeAttributeIndexer
from souper.soup import NodeTextIndexer
from souper.soup import Record
from souper.soup import get_soup
from zope.component import adapter
from zope.component.interfaces import ISite
from zope.interface import implementer
import datetime
import plone.api
import time
import uuid


DT_FORMAT = '%d.%m.%Y %H:%M'

# static uuid for the PortalRoot, as it doesn't have a uuid by default
UUID_PLONE_ROOT = '77c4390d-1179-44ba-9d57-46d23ac292c6'


@implementer(IUUID)
@adapter(IPloneSiteRoot)
def plone_root_uuid(context):
    """Adapter, which returns the static UUID for the IPloneSiteRoot, so that
    this uuid can be used to be indexed in our souper storage.
    """
    return UUID_PLONE_ROOT


def create_ordernumber():
    onum = hash(time.time())
    if onum < 0:
        return '0%s' % str(abs(onum))
    return '1%s' % str(onum)


def get_orders_soup(context):
    return get_soup('bda_plone_orders_orders', context)


def get_bookings_soup(context):
    return get_soup('bda_plone_orders_bookings', context)


def get_order(context, uid):
    if not isinstance(uid, uuid.UUID):
        uid = uuid.UUID(uid)
    soup = get_orders_soup(context)
    return [_ for _ in soup.query(Eq('uid', uid))][0]


def acquire_vendor_or_shop_root(context):
    """Returns the acquired vendor or the main shop by traversing up the
    content tree, starting from a context.

    :param context: The context to start searching for the nearest vendor.
    :type context: Content object
    :returns: The vendor, a shop item is belonging to.
    :rtype: Content object
    """
    while not IVendor.providedBy(context) and not ISite.providedBy(context):
        context = aq_parent(aq_inner(context))
    return context


def get_all_vendors():
    """Get all available vendor areas.

    :returns: Vendor area enabled content objects.
    :rtype: List of content objects.
    """
    cat = plone.api.portal.get_tool('portal_catalog')
    query = {'object_provides': IVendor.__identifier__}
    vendors = [brain.getObject() for brain in cat(**query)]
    return vendors + [plone.api.portal.get()]


def get_vendor_by_uid(context, vendor_uid):
    """Return vendor object by uid or site root as fallback if requested vendor
    not exists.

    :param vendor_uid: Vendor uid.
    :type vendor_uid: string or uuid.UUID object
    :returns: Vendor Object
    :rtype: IVendor implementing content Object
    """
    if not isinstance(vendor_uid, uuid.UUID):
        vendor_uid = uuid.UUID(vendor_uid)
    vendor = get_object_by_uid(vendor_uid)
    if vendor is None:
        vendor = plone.api.portal.get()
    return vendor


def get_vendors_for(user=None):
    """Gel all vendor containers a given or authenticated user has vendor
    permissions for.

    :param user: Optional user object to check permissions on vendor areas. If
                 no user object is give, the current user is used.
    :type user: MemberData object
    :returns: Allowed vendor area enabled content objects.
    :rtype: List of content objects.
    """
    if user is None:
        user = plone.api.user.get_current()
    def permitted(obj):
        return user.checkPermission(permissions.ModifyOrders, obj)
    return [vendor for vendor in get_all_vendors() if permitted(vendor)]


# TODO: no longer used right now
def get_vendor_order_uids(context, vendor_uid):
    """Get all order uids for a given vendor uid.

    :param vendor_uid: Vendor uid, which is used to filter the orders.
    :type vendor_uid: string or uuid.UUID object
    :returns: List of order UUID objects.
    :rtype: List of uuid.UUID
    """
    if vendor_uid and not isinstance(vendor_uid, uuid.UUID):
        vendor_uid = uuid.UUID(vendor_uid)
    soup = get_bookings_soup(context)
    res = soup.query(Eq('vendor_uid', vendor_uid))
    order_uids = set(booking.attrs['order_uid'] for booking in res)
    return order_uids


# TODO: used in vocabularies, remove if possible
def get_vendor_order_uids_for(context, user=None):
    """Get order uids all orders a given or current user has vendor
    permissions for.

    :param user: Optional user object to check permissions on vendor areas. If
                 no user object is give, the current user is used.
    :type user: MemberData object
    :returns: List of order UUID objects.
    :rtype: List of uuid.UUID
    """
    vendors = [uuid.UUID(IUUID(vendor)) for vendor in get_vendors_for(user)]
    soup = get_bookings_soup(context)
    res = soup.query(Any('vendor_uid', vendors))
    order_uids = set(booking.attrs['order_uid'] for booking in res)
    return order_uids


# TODO: no longer used right now
def get_customer_order_uids(context, customer):
    """Get all order uids for a given customer.

    :param creator: Customer aka user id aka creator.
    :type creator: string
    :returns: List of order UUID objects.
    :rtype: List of uuid.UUID
    """
    soup = get_orders_soup(context)
    res = soup.query(Eq('creator', customer))
    order_uids = set(order.attrs['uid'] for order in res)
    return order_uids


# TODO: no longer used right now
def get_customer_order_uids_for(context, user=None):
    """Get order uids of all orders a given or current user has made.

    :param user: Optional user object representing the customer. If
                 no user object is give, the current user is used.
    :type user: MemberData object
    :returns: List of order UUID objects.
    :rtype: List of uuid.UUID
    """
    if user is None:
        user = plone.api.user.get_current()
    return get_customer_order_uids(context, user.getId())


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
        vendor_uid_indexer = NodeAttributeIndexer('vendor_uid')
        catalog[u'vendor_uid'] = CatalogFieldIndex(vendor_uid_indexer)
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
        vendor_uids_indexer = NodeAttributeIndexer('vendor_uids')
        catalog[u'vendor_uids'] = CatalogKeywordIndex(vendor_uids_indexer)
        creator_indexer = NodeAttributeIndexer('creator')
        catalog[u'creator'] = CatalogFieldIndex(creator_indexer)
        created_indexer = NodeAttributeIndexer('created')
        catalog[u'created'] = CatalogFieldIndex(created_indexer)
        state_indexer = NodeAttributeIndexer('state')
        catalog[u'state'] = CatalogFieldIndex(state_indexer)
        salaried_indexer = NodeAttributeIndexer('salaried')
        catalog[u'salaried'] = CatalogFieldIndex(salaried_indexer)
        firstname_indexer = NodeAttributeIndexer('personal_data.firstname')
        catalog[u'personal_data.firstname'] = CatalogFieldIndex(
            firstname_indexer
        )
        lastname_indexer = NodeAttributeIndexer('personal_data.lastname')
        catalog[u'personal_data.lastname'] = CatalogFieldIndex(
            lastname_indexer
        )
        city_indexer = NodeAttributeIndexer('billing_address.city')
        catalog[u'billing_address.city'] = CatalogFieldIndex(city_indexer)
        search_attributes = ['personal_data.lastname',
                             'personal_data.firstname',
                             'billing_address.city',
                             'ordernumber']
        text_indexer = NodeTextIndexer(search_attributes)
        catalog[u'text'] = CatalogTextIndex(text_indexer)
        return catalog


# Flag whether to skip payment if items in cart are reserved. This behavior is
# desired i.e. for ticket shops, where a reserved ticket means that tickets are
# sold out, and only a reversal of an already sold ticket makes it possible to
# deliver it to a customer with a reservation; while in a product shop a
# reservation just usually means that an item is currently out of stock, and
# it just gets delivered later, so this flag can be set to ``False``.
SKIP_PAYMENT_IF_RESERVED = True


class OrderCheckoutAdapter(CheckoutAdapter):

    @instance_property
    def order(self):
        return Record()

    @property
    def vessel(self):
        return self.order.attrs

    @property
    def skip_payment(self):
        return SKIP_PAYMENT_IF_RESERVED \
            and self.order.attrs['state'] == 'reserved'

    @property
    def skip_payment_redirect_url(self):
        return '%s/@@reservation_done?uid=%s' % (self.context.absolute_url(),
                                                 self.order.attrs['uid'])

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
        member = plone.api.user.get_current()
        if member:
            creator = member.getId()
        created = datetime.datetime.now()
        order = self.order
        # XXX: payment name
        #      payment type
        #      payment total
        #      shipping name
        #      shipping vat
        sid = data.fetch('checkout.shipping_selection.shipping').extracted
        shipping = Shippings(self.context).get(sid)
        order.attrs['shipping'] = shipping.calculate(self.items)
        uid = order.attrs['uid'] = uuid.uuid4()
        order.attrs['creator'] = creator
        order.attrs['created'] = created
        order.attrs['salaried'] = 'no'
        bookings = self.create_bookings(order)
        booking_uids = list()
        vendor_uids = set()
        all_available = True
        for booking in bookings:
            booking_uids.append(booking.attrs['uid'])
            vendor_uids.add(booking.attrs['vendor_uid'])
            if booking.attrs['remaining_stock_available'] is not None\
                    and booking.attrs['remaining_stock_available'] < 0:
                all_available = False
        order.attrs['booking_uids'] = booking_uids
        order.attrs['vendor_uids'] = list(vendor_uids)
        order.attrs['state'] = all_available and 'new' or 'reserved'
        orders_soup = get_orders_soup(self.context)
        ordernumber = create_ordernumber()
        while self.ordernumber_exists(orders_soup, ordernumber):
            ordernumber = create_ordernumber()
        order.attrs['ordernumber'] = ordernumber
        orders_soup.add(order)
        bookings_soup = get_bookings_soup(self.context)
        for booking in bookings:
            bookings_soup.add(booking)
        return uid

    def create_bookings(self, order):
        ret = list()
        cart_data = get_data_provider(self.context)
        for uid, count, comment in self.items:
            booking = self.create_booking(
                order, cart_data, uid, count, comment)
            if booking:
                ret.append(booking)
        return ret

    def create_booking(self, order, cart_data, uid, count, comment):
        brain = get_catalog_brain(self.context, uid)
        # brain could be None if uid for item in cookie which no longer exists.
        if not brain:
            return
        buyable = brain.getObject()
        item_state = get_item_state(buyable, self.request)
        if not item_state.validate_count(item_state.aggregated_count):
            raise CheckoutError(u'Item no longer available')
        item_stock = get_item_stock(buyable)
        if item_stock.available is not None:
            item_stock.available -= float(count)
        item_data = get_item_data_provider(buyable)
        vendor = acquire_vendor_or_shop_root(buyable)
        booking = OOBTNode()
        booking.attrs['uid'] = uuid.uuid4()
        booking.attrs['buyable_uid'] = uid
        booking.attrs['buyable_count'] = count
        booking.attrs['buyable_comment'] = comment
        booking.attrs['order_uid'] = order.attrs['uid']
        booking.attrs['vendor_uid'] = uuid.UUID(IUUID(vendor))
        booking.attrs['creator'] = order.attrs['creator']
        booking.attrs['created'] = order.attrs['created']
        booking.attrs['exported'] = False
        booking.attrs['title'] = brain and brain.Title or 'unknown'
        booking.attrs['net'] = item_data.net
        booking.attrs['vat'] = item_data.vat
        booking.attrs['currency'] = cart_data.currency
        booking.attrs['quantity_unit'] = item_data.quantity_unit
        booking.attrs['remaining_stock_available'] = item_stock.available
        return booking


class OrderData(object):
    """Object for extracting order information.
    """

    def __init__(self, context, uid=None, order=None, vendor_uids=list()):
        """Create order data object by criteria

        :param uid: Order uid. XOR with order
        :type uid: string or uuid.UUID object
        :param order: Order record. XOR with uid
        :type order: souper.soup.Record object
        :param vendor_uids: Vendor uids, used to filter order bookings.
        :type vendor_uids: List of vendor uids as string or uuid.UUID object.
        """
        assert(uid and not order or order and not uid)
        if uid and not isinstance(uid, uuid.UUID):
            uid = uuid.UUID(uid)
        vendor_uids = [uuid.UUID(str(uid)) for uid in vendor_uids]
        self.context = context
        self._uid = uid
        self._order = order
        self.vendor_uids = vendor_uids

    @property
    def uid(self):
        if self._uid:
            return self._uid
        return self.order.attrs['uid']

    @property
    def order(self):
        if self._order:
            return self._order
        return get_order(self.context, self.uid)

    @property
    def bookings(self):
        soup = get_bookings_soup(self.context)
        query = Eq('order_uid', self.uid)
        if self.vendor_uids:
            query = query & Any('vendor_uid', self.vendor_uids)
        return soup.query(query)

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


class BuyableData(object):

    def __init__(self, context):
        assert IBuyable.providedBy(context)
        self.context = context

    def item_ordered(self, state=[]):
        """Return total count buyable item was ordered.
        """
        context = self.context
        bookings_soup = get_bookings_soup(context)
        order_bookings = dict()
        for booking in bookings_soup.query(Eq('buyable_uid', context.UID())):
            bookings = order_bookings.setdefault(
                booking.attrs['order_uid'], list())
            bookings.append(booking)
        orders_soup = get_orders_soup(context)
        count = Decimal('0')
        for order_uid, bookings in order_bookings.items():
            order = [_ for _ in orders_soup.query(Eq('uid', order_uid))][0]
            if not state:
                for booking in bookings:
                    count += booking.attrs['buyable_count']
            else:
                if order.attrs['state'] in state:
                    for booking in bookings:
                        count += booking.attrs['buyable_count']
        return count


@implementer(IPaymentData)
class PaymentData(object):

    def __init__(self, context):
        self.context = context

    @instance_property
    def order_data(self):
        return OrderData(self.context, uid=self.order_uid)

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
        amount = '%s %s' % (self.currency,
                            str(round(self.order_data.total, 2)))
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
        soup = get_orders_soup(self.context)
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
    # XXX: move concrete payment specific changes to bda.plone.payment and
    #      use ZCA for calling
    if event.payment.pid == 'six_payment':
        data = event.data
        order = get_order(event.context, event.order_uid)
        order.attrs['salaried'] = 'yes'
        order.attrs['tid'] = data['tid']


def payment_failed(event):
    # XXX: move concrete payment specific changes to bda.plone.payment and
    #      use ZCA for calling
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
        order_data = OrderData(self.context, uid=uid)
        order = order_data.order
        # XXX: currently we need to delete attribute before setting to a new
        #      value in order to persist change. fix in appropriate place.
        if transition == 'mark_salaried':
            del order.attrs['salaried']
            order.attrs['salaried'] = 'yes'
        elif transition == 'mark_outstanding':
            del order.attrs['salaried']
            order.attrs['salaried'] = 'no'
        elif transition == 'renew':
            del order.attrs['state']
            order.attrs['state'] = 'new'
            order_data.decrease_stock(order_data.bookings)
        elif transition == 'process':
            del order.attrs['state']
            order.attrs['state'] = 'processing'
        elif transition == 'finish':
            del order.attrs['state']
            order.attrs['state'] = 'finished'
        elif transition == 'cancel':
            del order.attrs['state']
            order.attrs['state'] = 'cancelled'
            order_data.increase_stock(order_data.bookings)
        else:
            raise ValueError(u"invalid transition: %s" % transition)
        soup = get_orders_soup(self.context)
        soup.reindex(records=[order])
        return order
