# -*- coding: utf-8 -*-
from bda.plone.orders import events
from bda.plone.orders import interfaces
from bda.plone.orders.common import BookingData
from zope.event import notify


def transitions_of_main_state(state):
    """List of transitions for a given orders or bookings main state
    """
    transitions = list()
    if state in [interfaces.STATE_NEW, interfaces.STATE_RESERVED]:
        transitions = [
            interfaces.STATE_TRANSITION_PROCESS,
            interfaces.STATE_TRANSITION_FINISH,
            interfaces.STATE_TRANSITION_CANCEL
        ]
    elif state == interfaces.STATE_MIXED:
        transitions = [
            interfaces.STATE_TRANSITION_PROCESS,
            interfaces.STATE_TRANSITION_FINISH,
            interfaces.STATE_TRANSITION_CANCEL,
            interfaces.STATE_TRANSITION_RENEW
        ]
    elif state == interfaces.STATE_PROCESSING:
        transitions = [
            interfaces.STATE_TRANSITION_FINISH,
            interfaces.STATE_TRANSITION_CANCEL,
            interfaces.STATE_TRANSITION_RENEW
        ]
    elif state is not None:
        transitions = [interfaces.STATE_TRANSITION_RENEW]
    else:  # empty dropdown
        transitions = []
    return transitions


def transitions_of_salaried_state(state):
    """List of transitions for a given orders or bookings salaried state
    """
    transitions = []
    if state == interfaces.SALARIED_YES:
        transitions = [interfaces.SALARIED_TRANSITION_OUTSTANDING]
    elif state == interfaces.SALARIED_NO:
        transitions = [interfaces.SALARIED_TRANSITION_SALARIED]
    else:
        transitions = [
            interfaces.SALARIED_TRANSITION_OUTSTANDING,
            interfaces.SALARIED_TRANSITION_SALARIED
        ]
    return transitions


def do_transition_for(order_state, transition, context=None, request=None):
    """Do any transition for given ``OrderState`` implementation.

    This mixes main state and salaried!
    """
    if transition == interfaces.SALARIED_TRANSITION_SALARIED:
        order_state.salaried = interfaces.SALARIED_YES

    elif transition == interfaces.SALARIED_TRANSITION_OUTSTANDING:
        order_state.salaried = interfaces.SALARIED_NO

    elif transition == interfaces.STATE_TRANSITION_RENEW:
        order_state.state = interfaces.STATE_NEW

    elif transition == interfaces.STATE_TRANSITION_PROCESS:
        order_state.state = interfaces.STATE_PROCESSING

    elif transition == interfaces.STATE_TRANSITION_FINISH:
        order_state.state = interfaces.STATE_FINISHED

    elif transition == interfaces.STATE_TRANSITION_CANCEL:
        bookings = getattr(order_state, 'bookings', [order_state])
        for booking_data in bookings:

            if not isinstance(booking_data, BookingData):
                # It's a booking record from iterating over ``bookings`` in
                # OrderData. We have to factorize a BookingData object now.
                booking_data = BookingData(
                    context=context,
                    booking=booking_data
                )
            booking_attrs = dict(booking_data.booking.attrs.items())
            # Set state to cancelled. This includes updat of OrderData state
            # and update of item_stock.
            booking_data.state = interfaces.STATE_CANCELLED
            # Send out event, which includes sending a notification mail
            event = events.BookingCancelledEvent(
                context=context,
                request=request,
                order_uid=booking_attrs['order_uid'],
                booking_attrs=booking_attrs,
            )
            notify(event)

    else:
        raise ValueError(u"Invalid transition: %s" % transition)
