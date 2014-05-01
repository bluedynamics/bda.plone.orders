from Acquisition import aq_parent
from Acquisition import aq_inner
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
from bda.plone.orders import interfaces as ifaces
from bda.plone.orders import message_factory as _
from bda.plone.orders.interfaces import IVendor
from bda.plone.payment import Payments
from bda.plone.payment.interfaces import IPaymentData
from bda.plone.shipping import Shippings
from bda.plone.shipping.interfaces import IShippingItem
from bda.plone.shop.interfaces import IBuyable # XXX: dependency inversion
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
from zope.component.interfaces import ISite
from zope.interface import implementer
import datetime
import plone.api
import time
import uuid


DT_FORMAT = '%d.%m.%Y %H:%M'


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
    vendor = get_object_by_uid(context, vendor_uid)
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


def get_vendor_uids_for(user=None):
    """Gel all vendor container uids a given or authenticated user has vendor
    permissions for.

    :param user: Optional user object to check permissions on vendor areas. If
                 no user object is give, the current user is used.
    :type user: MemberData object
    :returns: Allowed vendor area uids for given or authenticated member.
    :rtype: List of uuid.UUID objects.
    """
    return [uuid.UUID(IUUID(vendor)) for vendor in get_vendors_for(user=user)]


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
    vendors = get_vendor_uids_for(user=user)
    soup = get_bookings_soup(context)
    res = soup.query(Any('vendor_uid', vendors))
    order_uids = set(booking.attrs['order_uid'] for booking in res)
    return order_uids


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
        state_indexer = NodeAttributeIndexer('state')
        catalog[u'state'] = CatalogFieldIndex(state_indexer)
        salaried_indexer = NodeAttributeIndexer('salaried')
        catalog[u'salaried'] = CatalogFieldIndex(salaried_indexer)
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
        firstname_indexer = NodeAttributeIndexer('personal_data.firstname')
        catalog[u'personal_data.firstname'] = \
            CatalogFieldIndex(firstname_indexer)
        lastname_indexer = NodeAttributeIndexer('personal_data.lastname')
        catalog[u'personal_data.lastname'] = \
            CatalogFieldIndex(lastname_indexer)
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
        return Record()

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
        order = self.order
        # order UUID
        uid = order.attrs['uid'] = uuid.uuid4()
        # order creator
        creator = None
        member = plone.api.user.get_current()
        if member:
            creator = member.getId()
        order.attrs['creator'] = creator
        # order creation date
        created = datetime.datetime.now()
        order.attrs['created'] = created
        cart_data = get_data_provider(self.context, self.request)
        # payment related information
        if cart_data.total > Decimal(0):
            payment_param = 'checkout.payment_selection.payment'
            pid = data.fetch(payment_param).extracted
            payment = Payments(self.context).get(pid)
            order.attrs['payment_method'] = pid
            if payment:
                order.attrs['payment_label'] = payment.label
            else:
                order.attrs['payment_label'] = _('unknown', default=u'Unknown')
        # no payment
        else:
            order.attrs['payment_method'] = 'no_payment'
            order.attrs['payment_label'] = _('no_payment',
                                             default=u'No Payment')
        # shipping related information
        if cart_data.include_shipping_costs:
            shipping_param = 'checkout.shipping_selection.shipping'
            sid = data.fetch(shipping_param).extracted
            shipping = Shippings(self.context).get(sid)
            order.attrs['shipping_method'] = sid
            order.attrs['shipping_label'] = shipping.label
            order.attrs['shipping_description'] = shipping.description
            try:
                shipping_net = shipping.net(self.items)
                shipping_vat = shipping.vat(self.items)
                order.attrs['shipping_net'] = shipping_net
                order.attrs['shipping_vat'] = shipping_vat
                order.attrs['shipping'] = shipping_net + shipping_vat
            # B/C for bda.plone.shipping < 0.4
            except NotImplementedError:
                shipping_net = shipping.calculate(self.items)
                order.attrs['shipping_net'] = shipping_net
                order.attrs['shipping_vat'] = Decimal(0)
                order.attrs['shipping'] = shipping_net
        # no shipping
        else:
            order.attrs['shipping_method'] = 'no_shipping'
            order.attrs['shipping_label'] = _('no_shipping',
                                              default=u'No Shipping')
            order.attrs['shipping_description'] = ''
            order.attrs['shipping_net'] = Decimal(0)
            order.attrs['shipping_vat'] = Decimal(0)
            order.attrs['shipping'] = Decimal(0)
        # create order bookings
        bookings = self.create_bookings(order)
        # lookup booking uids and vendor uids
        booking_uids = list()
        vendor_uids = set()
        for booking in bookings:
            booking_uids.append(booking.attrs['uid'])
            vendor_uids.add(booking.attrs['vendor_uid'])
        order.attrs['booking_uids'] = booking_uids
        order.attrs['vendor_uids'] = list(vendor_uids)
        # cart discount related information
        cart_discount = cart_data.discount(self.items)
        order.attrs['cart_discount_net'] = cart_discount['net']
        order.attrs['cart_discount_vat'] = cart_discount['vat']
        # create ordernumber
        orders_soup = get_orders_soup(self.context)
        ordernumber = create_ordernumber()
        while self.ordernumber_exists(orders_soup, ordernumber):
            ordernumber = create_ordernumber()
        order.attrs['ordernumber'] = ordernumber
        # add order
        orders_soup.add(order)
        # add bookings
        bookings_soup = get_bookings_soup(self.context)
        for booking in bookings:
            bookings_soup.add(booking)
        # return uid of added order
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
        available = item_stock.available
        state = (available is None or available >= 0) and ifaces.STATE_NEW\
            or ifaces.STATE_RESERVED
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
        booking.attrs['discount_net'] = item_data.discount_net(count)
        booking.attrs['currency'] = cart_data.currency
        booking.attrs['quantity_unit'] = item_data.quantity_unit
        booking.attrs['remaining_stock_available'] = available
        booking.attrs['state'] = state
        booking.attrs['salaried'] = ifaces.SALARIED_NO
        booking.attrs['tid'] = 'none'
        booking.attrs['shippable'] = IShippingItem(buyable).shippable
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
        assert(bool(uid) != bool(order))  # ^= xor
        if uid and not isinstance(uid, uuid.UUID):
            uid = uuid.UUID(uid)
        vendor_uids = [uuid.UUID(str(vuid)) for vuid in vendor_uids]
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
    def currency(self):
        ret = None
        for booking in self.bookings:
            val = booking.attrs['currency']
            if ret and ret != val:
                msg = 'Order contains bookings with inconsistent ' +\
                      'currencies {0} != {1}'.format(ret, val)
                raise ValueError(msg)
            ret = val
        return ret

    @property
    def state(self):
        ret = None
        for booking in self.bookings:
            val = booking.attrs['state']
            if ret and ret != val:
                ret = ifaces.STATE_MIXED
                break
            else:
                ret = val
        return ret

    @state.setter
    def state(self, value):
        for booking in self.bookings:
            booking.attrs['state'] = value

    @property
    def salaried(self):
        ret = None
        for booking in self.bookings:
            val = booking.attrs['salaried']
            if ret and ret != val:
                ret = ifaces.SALARIED_MIXED
                break
            else:
                ret = val
        return ret

    @salaried.setter
    def salaried(self, value):
        for booking in self.bookings:
            booking.attrs['salaried'] = value

    @property
    def tid(self):
        ret = set()
        for booking in self.bookings:
            tid = booking.attrs.get('tid', None)
            if tid:
                ret.add(tid)
        return ret

    @tid.setter
    def tid(self, value):
        for booking in self.bookings:
            booking.attrs['tid'] = value

    @property
    def net(self):
        # XXX: use decimal
        ret = 0.0
        for booking in self.bookings:
            count = float(booking.attrs['buyable_count'])
            net = booking.attrs.get('net', 0.0)
            discount_net = float(booking.attrs['discount_net'])
            ret += (net - discount_net) * count
        return ret

    @property
    def vat(self):
        # XXX: use decimal
        ret = 0.0
        for booking in self.bookings:
            count = float(booking.attrs['buyable_count'])
            net = booking.attrs.get('net', 0.0)
            discount_net = float(booking.attrs['discount_net'])
            item_net = net - discount_net
            ret += (item_net * booking.attrs.get('vat', 0.0) / 100.0) * count
        return ret

    @property
    def discount_net(self):
        # XXX: use decimal
        return float(self.order.attrs['cart_discount_net'])

    @property
    def discount_vat(self):
        # XXX: use decimal
        return float(self.order.attrs['cart_discount_vat'])

    @property
    def shipping_net(self):
        # XXX: use decimal
        return float(self.order.attrs['shipping_net'])

    @property
    def shipping_vat(self):
        # XXX: use decimal
        return float(self.order.attrs['shipping_vat'])

    @property
    def shipping(self):
        # XXX: use decimal
        return float(self.order.attrs['shipping'])

    @property
    def total(self):
        # XXX: use decimal
        total = self.net - self.discount_net + self.vat - self.discount_vat
        return total + self.shipping

    def increase_stock(self, bookings):
        for booking in bookings:
            obj = get_object_by_uid(self.context, booking.attrs['buyable_uid'])
            # object no longer exists
            if not obj:
                continue
            stock = get_item_stock(obj)
            # if stock.available is None, no stock information used
            if stock.available is not None:
                stock.available += float(booking.attrs['buyable_count'])

    def decrease_stock(self, bookings):
        for booking in bookings:
            obj = get_object_by_uid(self.context, booking.attrs['buyable_uid'])
            # object no longer exists
            if not obj:
                continue
            stock = get_item_stock(obj)
            # if stock.available is None, no stock information used
            if stock.available is not None:
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
        for booking in bookings_soup.query(Eq('buyable_uid', IUUID(context))):
            bookings = order_bookings.setdefault(
                booking.attrs['order_uid'], list())
            bookings.append(booking)
        count = Decimal('0')
        for order_uid, bookings in order_bookings.items():
            for booking in bookings:
                if state and booking.attrs['state'] not in state:
                    continue
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
        return self.order_data.currency

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
        order = OrderData(event.context, uid=event.order_uid)
        order.salaried = ifaces.SALARIED_YES
        order.tid = data['tid']


def payment_failed(event):
    # XXX: move concrete payment specific changes to bda.plone.payment and
    #      use ZCA for calling
    if event.payment.pid == 'six_payment':
        data = event.data
        order = OrderData(event.context, uid=event.order_uid)
        order.salaried = ifaces.SALARIED_FAILED
        order.tid = data['tid']


class OrderTransitions(object):

    def __init__(self, context, vendor_uids=list()):
        self.context = context

    def do_transition(self, uid, vendor_uids, transition):
        """Do transition for order by UID and transition name.

        @param uid: uuid.UUID or string representing a UUID
        @param vendor_uids: list of uuid.UUID objects
        @param transition: string

        @return: order record
        """
        if not isinstance(uid, uuid.UUID):
            uid = uuid.UUID(uid)
        order_data = OrderData(self.context, uid=uid, vendor_uids=vendor_uids)
        order = order_data.order
        for booking in order_data.bookings:
            self.do_transition_for_booking(booking, transition)
        if transition == ifaces.STATE_TRANSITION_RENEW:
            order_data.decrease_stock(order_data.bookings)
        elif transition == ifaces.STATE_TRANSITION_CANCEL:
            order_data.increase_stock(order_data.bookings)
        orders_soup = get_orders_soup(self.context)
        orders_soup.reindex(records=[order])
        return order

    def do_transition_for_booking(self, booking, transition):
        # XXX: currently we need to delete attribute before setting to a new
        #      value in order to persist change. fix in appropriate place.
        if transition == ifaces.SALARIED_TRANSITION_SALARIED:
            del booking.attrs['salaried']
            booking.attrs['salaried'] = ifaces.SALARIED_YES
        elif transition == ifaces.SALARIED_TRANSITION_OUTSTANDING:
            del booking.attrs['salaried']
            booking.attrs['salaried'] = ifaces.SALARIED_NO
        elif transition == ifaces.STATE_TRANSITION_RENEW:
            del booking.attrs['state']
            booking.attrs['state'] = ifaces.STATE_NEW
        elif transition == ifaces.STATE_TRANSITION_PROCESS:
            del booking.attrs['state']
            booking.attrs['state'] = ifaces.STATE_PROCESSING
        elif transition == ifaces.STATE_TRANSITION_FINISH:
            del booking.attrs['state']
            booking.attrs['state'] = ifaces.STATE_FINISHED
        elif transition == ifaces.STATE_TRANSITION_CANCEL:
            del booking.attrs['state']
            booking.attrs['state'] = ifaces.STATE_CANCELLED
        else:
            raise ValueError(u"invalid transition: %s" % transition)
        bookings_soup = get_bookings_soup(self.context)
        bookings_soup.reindex(records=[booking])
