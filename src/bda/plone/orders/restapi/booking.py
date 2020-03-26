# -*- coding: utf-8 -*-
from bda.plone.cart.restapi.service import TraversingService
from bda.plone.orders.interfaces import workflow
from bda.plone.orders.common import get_vendor_uids_for
from bda.plone.orders.datamanagers.booking import BookingData
from plone.restapi.interfaces import ISerializeToJson
from zope.component import getMultiAdapter


class BookingService(TraversingService):
    """Single Booking"""

    def process_request(self, booking_data):
        pass

    def reply(self):
        if len(self.params) != 1:
            raise Exception(
                "Must supply exactly one UID (unique identifier of"
                "the booking) to be retrieved as last part of the URL ."
            )
        booking_data = BookingData(self.context, uid=self.params[0])
        if booking_data.booking is None:
            raise ValueError("Can not find given UID '{0}'".format(self.params[0]))
        import pdb; pdb.set_trace()
        self.process_request(booking_data)
        serializer = getMultiAdapter((booking_data, self.request), ISerializeToJson)
        return serializer()


class BookingUpdateService(BookingService):
    """Single Booking update: state and salaried"""

    def process_request(self, booking_data):
        salaried = self.request.form.get("salaried", booking_data.salaried)
        if salaried not in [
            workflow.SALARIED_YES,
            workflow.SALARIED_NO,
            workflow.SALARIED_FAILED,
        ]:
            raise Exception(
                "salaried must be one out of: {0}, {1}, {2}.".format(
                    workflow.SALARIED_YES,
                    workflow.SALARIED_NO,
                    workflow.SALARIED_FAILED,
                )
            )
        if salaried != booking_data.salaried:
            booking_data.salaried = salaried

        state = self.request.form.get("state", booking_data.state)
        if state not in [
            workflow.STATE_CANCELLED,
            workflow.STATE_FINISHED,
            workflow.STATE_NEW,
            workflow.STATE_PROCESSING,
            workflow.STATE_RESERVED,
        ]:
            raise Exception(
                "state must be one out of: {0}, {1}, {2}, {3}, {4}.".format(
                    workflow.STATE_CANCELLED,
                    workflow.STATE_FINISHED,
                    workflow.STATE_NEW,
                    workflow.STATE_PROCESSING,
                    workflow.STATE_RESERVED,
                )
            )
        if state != booking_data.state:
            booking_data.state = state
