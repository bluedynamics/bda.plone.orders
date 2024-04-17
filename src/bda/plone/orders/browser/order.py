# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from bda.plone.ajax import ajax_continue
from bda.plone.ajax import AjaxAction
from bda.plone.cart.utils import ascur
from bda.plone.cart.utils import get_object_by_uid
from bda.plone.checkout import message_factory as _co
from bda.plone.checkout.vocabularies import get_pycountry_name
from bda.plone.orders import interfaces as ifaces
from bda.plone.orders import message_factory as _
from bda.plone.orders import permissions
from bda.plone.orders import vocabularies as vocabs
from bda.plone.orders.browser.common import ContentTemplateView
from bda.plone.orders.common import DT_FORMAT
from bda.plone.orders.common import get_orders_soup
from bda.plone.orders.common import get_vendor_by_uid
from bda.plone.orders.common import get_vendor_uids_for
from bda.plone.orders.datamanagers.booking import booking_update_comment
from bda.plone.orders.datamanagers.booking import BookingData
from bda.plone.orders.datamanagers.order import OrderData
from bda.plone.orders.transitions import do_transition_for
from plone.memoize import view
from plone.protect.utils import addTokenToUrl
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from repoze.catalog.query import Eq
from yafowil.base import factory
from yafowil.controller import Controller
from zExceptions import BadRequest
from zExceptions import Redirect
from zope.i18n import translate
from zope.security import checkPermission

import plone.api
import uuid


###############################################################################
# order related base classes
# XXX: used by order and invoice views. maybe generalize
###############################################################################


class OrderDataView(BrowserView):
    """Base view for displaying order related data.
    """

    @property
    @view.memoize
    def order_data(self):
        return OrderData(self.context, uid=self.uid)

    @property
    def uid(self):
        # case order uid has been set manually
        try:
            return self._uid
        # fallback to lookup order uid on request
        except AttributeError:
            return self.request.form.get("uid", None)

    @uid.setter
    def uid(self, value):
        self._uid = value

    @property
    def order(self):
        if not self.uid:
            err = _(
                "statusmessage_err_no_order_uid_given",
                default="Cannot show order information because no order uid was given.",  # noqa
            )
            IStatusMessage(self.request).addStatusMessage(err, "error")
            raise Redirect(self.context.absolute_url())
        return dict(self.order_data.order.attrs)

    def country(self, country_id):
        # return value if no id not available i.e. if no dropdown in use
        try:
            return get_pycountry_name(country_id)
        except Exception:
            return country_id


class ProtectedOrderDataView(ContentTemplateView):
    """Protected order data view.

    Expect ordernumber and email to grant access to view details.
    """

    view_template = ViewPageTemplateFile("templates/protected_view.pt")
    content_template = None
    uid = None
    ordernumber = ""
    email = ""
    wrapper_css = "protected_order_data"

    def _form_handler(self, widget, data):
        self.ordernumber = data["ordernumber"].extracted
        self.email = data["email"].extracted

    def render_auth_form(self):
        # Render the authentication form for anonymous users.
        req = self.request
        action = req.getURL()
        ordernumber = self.ordernumber or req.form.get("ordernumber", "")
        email = self.email or req.form.get("email", "")
        form = factory("form", name="content_auth_form", props={"action": action})
        form["ordernumber"] = factory(
            "div:label:error:text",
            value=ordernumber,
            props={
                "label": _("anon_auth_label_ordernumber", default=u"Ordernumber"),
                "div.class": "ordernumber",
                "required": True,
            },
        )
        form["email"] = factory(
            "div:label:error:text",
            value=email,
            props={
                "label": _("anon_auth_label_email", default=u"Email"),
                "div.class": "email",
                "required": True,
            },
        )
        form["submit"] = factory(
            "button",
            props={
                "type": "submit",
                "text": _("anon_auth_label_submit", default=u"Submit"),
                "class": "btn btn-secondary mt-3",
                "handler": self._form_handler,
                "action": "submit",
            },
        )
        controller = Controller(form, req)
        return controller.rendered

    def __call__(self):
        req = self.request
        ordernumber = req.form.get("content_auth_form.ordernumber", None)
        email = req.form.get("content_auth_form.email", None)
        order = None
        errs = []
        if ordernumber and email:
            orders_soup = get_orders_soup(self.context)
            order = orders_soup.query(Eq("ordernumber", ordernumber))
            try:
                # generator should have only one item
                order = next(order)
                try:
                    assert order.attrs["personal_data.email"] == email
                except AssertionError:
                    # Don't raise Unauthorized, as this allows to draw
                    # conclusions on existing ordernumbers
                    order = None
            except StopIteration:
                # order by ordernumber not exists
                order = None
        if not email:
            err = _(
                "anon_auth_err_email",
                default=u"Please provide the email adress you used for "
                u"submitting the order.",
            )
            errs.append(err)
        if not ordernumber:
            err = _(
                "anon_auth_err_ordernumber", default=u"Please provide the ordernumber"
            )
            errs.append(err)
        if email and ordernumber and not order:
            err = _(
                "anon_auth_err_order",
                default=u"No order could be found for the given " u"credentials",
            )
            errs.append(err)
        if not ordernumber and not email:
            # first call of this form
            errs = []
        for err in errs:
            IStatusMessage(self.request).addStatusMessage(err, "error")
        self.uid = order.attrs["uid"] if order else None
        return self.view_template(self)


###############################################################################
# order actions
###############################################################################


class BookingCancel(BrowserView):
    """Cancel booking action.
    """

    def __call__(self):
        booking_uid = self.request.form.get("uid")
        if not booking_uid:
            raise BadRequest("value not given")
        try:
            booking_data = BookingData(self.context, uid=uuid.UUID(booking_uid))  # noqa
            if booking_data.booking is None:
                raise ValueError("invalid value (no booking found)")
            do_transition_for(
                booking_data,
                transition=ifaces.STATE_TRANSITION_CANCEL,
                context=self.context,
                request=self.request,
            )
        except ValueError:
            raise BadRequest("something is wrong with the value")
        order_uid = booking_data.booking.attrs["order_uid"]
        target = u"{}?uid={}".format(self.context.absolute_url(), order_uid)
        action = AjaxAction(
            target=target, name="order", mode="replace", selector=".order_details"
        )
        ajax_continue(self.request, action)


class BookingUpdateComment(BrowserView):
    """Update boking comment action.
    """

    def __call__(self):
        booking_uid = self.request.form.get("uid")
        if not booking_uid:
            raise BadRequest("value not given")
        booking_comment = self.request.form.get("comment")
        try:
            booking_update_comment(self, uuid.UUID(booking_uid), booking_comment)
        except ValueError:
            raise BadRequest("something is wrong with the value")


###############################################################################
# order details
###############################################################################


class OrderViewBase(OrderDataView):
    """Base view for displaying order details.
    """

    @property
    def net(self):
        return ascur(self.order_data.net)

    @property
    def vat(self):
        return ascur(self.order_data.vat)

    @property
    def discount_net(self):
        return ascur(self.order_data.discount_net)

    @property
    def discount_vat(self):
        return ascur(self.order_data.discount_vat)

    @property
    def shipping_title(self):
        # XXX: node.ext.zodb or souper bug with double linked list. figure out
        order = self.order_data.order.attrs
        # order = self.order
        title = translate(order["shipping_label"], context=self.request)
        if order["shipping_description"]:
            title += " (%s)" % translate(
                order["shipping_description"], context=self.request
            )
        return title

    @property
    def shipping_net(self):
        return ascur(self.order_data.shipping_net)

    @property
    def shipping_vat(self):
        return ascur(self.order_data.shipping_vat)

    @property
    def shipping(self):
        # B/C
        return ascur(self.order_data.shipping)

    @property
    def total(self):
        return ascur(self.order_data.total)

    @property
    def currency(self):
        currency = None
        for booking in self.order_data.bookings:
            if currency is None:
                currency = booking.attrs.get("currency")
            if currency != booking.attrs.get("currency"):
                return None
        return currency

    @property
    def listing(self):
        # XXX: discount
        can_cancel_booking = self.can_cancel_booking
        ret = list()
        for booking in self.order_data.bookings:
            obj = get_object_by_uid(self.context, booking.attrs["buyable_uid"])
            state = vocabs.state_vocab()[booking.attrs.get("state")]
            salaried = vocabs.salaried_vocab()[booking.attrs.get("salaried")]
            cancel_target = None
            if can_cancel_booking and state != ifaces.STATE_CANCELLED:
                cancel_target = addTokenToUrl(
                    "{}?uid={}".format(
                        self.context.absolute_url(), booking.attrs["uid"]
                    )
                )
            ret.append(
                {
                    "uid": booking.attrs["uid"],
                    "title": booking.attrs["title"],
                    "url": obj.absolute_url() if obj else None,
                    "cancel_target": cancel_target,
                    "count": booking.attrs["buyable_count"],
                    "net": ascur(booking.attrs.get("net", 0.0)),
                    "discount_net": ascur(float(booking.attrs["discount_net"])),
                    "vat": booking.attrs.get("vat", 0.0),
                    "comment": booking.attrs["buyable_comment"],
                    "quantity_unit": booking.attrs.get("quantity_unit"),
                    "currency": booking.attrs.get("currency"),
                    "state": state,
                    "salaried": salaried,
                }
            )
        return ret

    @property
    def can_modify_order(self):
        return checkPermission("bda.plone.orders.ModifyOrders", self.context)

    @property
    def can_cancel_booking(self):
        return self.can_modify_order and self.order_data.state != ifaces.STATE_CANCELLED

    @property
    def gender(self):
        gender = self.order.get("personal_data.gender", _co("unknown", "Unknown"))
        if gender == "male":
            return _co("male", "Male")
        if gender == "female":
            return _co("female", "Female")
        return gender

    @property
    def payment(self):
        # XXX: node.ext.zodb or souper bug with double linked list. figure out
        order = self.order_data.order.attrs
        # order = self.order
        title = translate(order["payment_label"], context=self.request)
        return title

    @property
    def salaried(self):
        salaried = self.order_data.salaried or ifaces.SALARIED_NO
        return vocabs.salaried_vocab()[salaried]

    @property
    def tid(self):
        tid = [it for it in self.order_data.tid if it != "none"]
        if not tid:
            return _("none", default=u"None")
        return ", ".join(tid)

    @property
    def state(self):
        state = self.order_data.state or ifaces.STATE_NEW
        return vocabs.state_vocab()[state]

    @property
    def created(self):
        value = self.order.get("created", _("unknown", default=u"Unknown"))
        if value:
            value = value.strftime(DT_FORMAT)
        return value

    def exported(self, item):
        return item["exported"] and _("yes", default=u"Yes") or _("no", default=u"No")


class OrderView(OrderViewBase):
    def __call__(self):
        vendor_uid = self.request.form.get("vendor", "")
        if vendor_uid:
            self.vendor_uids = [vendor_uid]
            vendor = get_vendor_by_uid(self.context, vendor_uid)
            user = plone.api.user.get_current()
            if not user.checkPermission(permissions.ModifyOrders, vendor):
                raise Unauthorized
        else:
            self.vendor_uids = get_vendor_uids_for()
            if not self.vendor_uids:
                raise Unauthorized
        return super(OrderView, self).__call__()

    @property
    @view.memoize
    def order_data(self):
        return OrderData(self.context, uid=self.uid, vendor_uids=self.vendor_uids)

    @property
    def ordernumber(self):
        return self.order_data.order.attrs["ordernumber"]


class MyOrderView(OrderViewBase):
    def __call__(self):
        # check if order was created by authenticated user
        user = plone.api.user.get_current()
        if user.getId() != self.order["creator"]:
            raise Unauthorized
        return super(MyOrderView, self).__call__()

    @property
    def ordernumber(self):
        return self.order_data.order.attrs["ordernumber"]


class DirectOrderView(OrderViewBase, ProtectedOrderDataView):
    content_template = ViewPageTemplateFile("templates/order.pt")
