# -*- coding: utf-8 -*-
from bda.plone.orders import safe_encode
from bda.plone.orders.interfaces import workflow
from bda.plone.orders.common import get_orders_soup
from bda.plone.orders.common import DT_FORMAT
from bda.plone.orders.datamanagers.order import OrderData
from bda.plone.payment.interfaces import IPaymentData
from node.utils import instance_property
from persistent.dict import PersistentDict
from repoze.catalog.query import Eq
from zope.interface import implementer

import six


@implementer(IPaymentData)
class PaymentData(object):
    def __init__(self, context):
        self.context = context

    @instance_property
    def order_data(self):
        return OrderData(self.context, uid=self.order_uid)

    @property
    def amount(self):
        amount = "%0.2f" % self.order_data.total
        amount = amount[: amount.index(".")] + amount[amount.index(".") + 1 :]
        return amount

    @property
    def currency(self):
        return self.order_data.currency

    @property
    def description(self):
        order = self.order_data.order
        attrs = order.attrs
        if six.PY2:
            amount = safe_encode(
                "%s %s" % (self.currency, str(round(self.order_data.total, 2)))
            )
        else:
            amount = "%s %s" % (self.currency, str(round(self.order_data.total, 2)))
        description = ", ".join(
            [
                attrs["created"].strftime(DT_FORMAT),
                attrs["personal_data.firstname"],
                attrs["personal_data.lastname"],
                attrs["billing_address.city"],
                amount,
            ]
        )
        return description

    @property
    def ordernumber(self):
        return self.order_data.order.attrs["ordernumber"]

    def annotations(self, ordernumber):
        self.order_uid = self.uid_for(ordernumber)
        attrs = self.order_data.order.attrs
        if "annotations" not in attrs:
            attrs["annotations"] = PersistentDict()
        return attrs["annotations"]

    def uid_for(self, ordernumber):
        soup = get_orders_soup(self.context)
        for order in soup.query(Eq("ordernumber", ordernumber)):
            return str(order.attrs["uid"])

    def data(self, order_uid):
        self.order_uid = order_uid
        return {
            "amount": self.amount,
            "currency": self.currency,
            "description": self.description,
            "ordernumber": self.ordernumber,
        }


def _payment_handling(event, state):
    data = event.data
    order = OrderData(event.context, uid=event.order_uid)
    order.salaried = state
    # XXX: move concrete payment specific changes to bda.plone.payment.
    # Payment may provide a tid attribute to be used here.
    if event.payment.pid == "six_payment":
        order.tid = data["tid"]
    elif event.payment.pid == "stripe_payment":
        order.tid = data["charge_id"]


def payment_success(event):
    _payment_handling(event, workflow.SALARIED_YES)


def payment_failed(event):
    _payment_handling(event, workflow.SALARIED_FAILED)
