# -*- coding: utf-8 -*-
from bda.plone.orders import interfaces as ifaces
from bda.plone.orders import message_factory as _
from bda.plone.orders.common import OrderData
from Products.Five import BrowserView


###############################################################################
# views
###############################################################################


class OrderDone(BrowserView):
    """Landing page after order has been done.
    """

    # XXX: provide different headings and texts for states reservation and
    #      mixed
    reservation_states = (ifaces.STATE_RESERVED, ifaces.STATE_MIXED)

    @property
    def order_data(self):
        return OrderData(self.context, uid=self.request.get('uid'))

    @property
    def heading(self):
        try:
            if self.order_data.state in self.reservation_states:
                return _('reservation_done', default=u'Reservation Done')
            return _('order_done', default=u'Order Done')
        except ValueError:
            return _('unknown_order', default=u'Unknown Order')

    @property
    def id(self):
        try:
            return self.order_data.order.attrs['ordernumber']
        except ValueError:
            return _('unknown', default=u'Unknown')

    @property
    def text(self):
        try:
            if self.order_data.state in self.reservation_states:
                return _('reservation_text', default=u'Thanks for your Reservation.')
            return _('order_text', default=u'Thanks for your Order.')
        except ValueError:
            return _('unknown_order_text', default=u'Sorry, this order does not exist.')
