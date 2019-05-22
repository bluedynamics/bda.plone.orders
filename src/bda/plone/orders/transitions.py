# -*- coding: utf-8 -*-
from bda.plone.orders import events
from bda.plone.orders.datamanager.booking import BookingData
from bda.plone.orders.interfaces import workflow
from zope.event import notify


"""
State transitions and stock change

origin state    target state    stock change
============================================
NEW             PROCESSING      0
NEW             FINISHED        0
NEW             CANCELLED       +1
RESERVED        PROCESSING      -1
RESERVED        FINISHED        -1
RESERVED        CANCELLED       0
PROCESSING      FINISH          0
PROCESSING      CANCEL          +1
PROCESSING      RENEW           0
FINISHED        RENEW           0
CANCELLED       RENEW           -1

"""


def transitions_of_main_state(state):
    """List of transitions for a given orders or bookings main state
    """
    transitions = list()
    if state in [workflow.STATE_NEW, workflow.STATE_RESERVED]:
        transitions = [
            workflow.STATE_TRANSITION_PROCESS,
            workflow.STATE_TRANSITION_FINISH,
            workflow.STATE_TRANSITION_CANCEL,
        ]
    elif state == workflow.STATE_MIXED:
        transitions = [
            workflow.STATE_TRANSITION_PROCESS,
            workflow.STATE_TRANSITION_FINISH,
            workflow.STATE_TRANSITION_CANCEL,
            workflow.STATE_TRANSITION_RENEW,
        ]
    elif state == workflow.STATE_PROCESSING:
        transitions = [
            workflow.STATE_TRANSITION_FINISH,
            workflow.STATE_TRANSITION_CANCEL,
            workflow.STATE_TRANSITION_RENEW,
        ]
    elif state is not None:
        transitions = [workflow.STATE_TRANSITION_RENEW]
    else:  # empty dropdown
        transitions = []
    return transitions


def transitions_of_salaried_state(state):
    """List of transitions for a given orders or bookings salaried state
    """
    transitions = []
    if state == workflow.SALARIED_YES:
        transitions = [workflow.SALARIED_TRANSITION_OUTSTANDING]
    elif state == workflow.SALARIED_NO:
        transitions = [workflow.SALARIED_TRANSITION_SALARIED]
    else:
        transitions = [
            workflow.SALARIED_TRANSITION_OUTSTANDING,
            workflow.SALARIED_TRANSITION_SALARIED,
        ]
    return transitions


def do_transition_for(order_state, transition, context=None, request=None):
    """Do any transition for given ``OrderState`` implementation.

    This mixes main state and salaried!
    """

    def _set_state(
        data,
        state_value,
        state_attr="state",
        event_class=None,
        event_emit_on_last=False,
    ):
        #
        #                             Case BookingData
        #                    Case OrderData    |
        # BookingData or OrderData    |        |
        #                   V         V        V
        bookings = getattr(data, "bookings", [data])
        bookings = list(bookings)  # make list out of generator to have a len
        bookings_len = len(bookings)
        for cnt, booking_data in enumerate(bookings):

            if not isinstance(booking_data, BookingData):
                # Case OrderData
                # It's a booking record from iterating over ``bookings`` in
                # OrderData. We have to factorize a BookingData object now.
                booking_data = BookingData(context=context, booking=booking_data)

            # Set state. This includes updates via it's setter method (E.g.
            # OrderData state and item_stock).
            setattr(booking_data, state_attr, state_value)

            # Optionally send out event.
            # May include sending out a notification mail.
            if event_class and (
                cnt == bookings_len - 1
                or not event_emit_on_last  # event_emit_on_last  # or emit always
            ):
                booking_attrs = dict(list(booking_data.booking.attrs.items()))
                event = event_class(
                    context=context,
                    request=request,
                    order_uid=booking_attrs["order_uid"],
                    booking_attrs=booking_attrs,
                )
                notify(event)

    if transition == workflow.SALARIED_TRANSITION_SALARIED:
        _set_state(order_state, workflow.SALARIED_YES, "salaried")

    elif transition == workflow.SALARIED_TRANSITION_OUTSTANDING:
        _set_state(order_state, workflow.SALARIED_NO, "salaried")

    elif transition == workflow.STATE_TRANSITION_RENEW:
        _set_state(
            order_state,
            workflow.STATE_NEW,
            event_class=events.OrderSuccessfulEvent,
            event_emit_on_last=True,
        )

    elif transition == workflow.STATE_TRANSITION_PROCESS:
        event_class = None
        if order_state.state == workflow.STATE_RESERVED:
            event_class = events.BookingReservedToOrderedEvent
        _set_state(
            order_state, workflow.STATE_PROCESSING, event_class=event_class
        )  # noqa

    elif transition == workflow.STATE_TRANSITION_FINISH:
        event_class = None
        if order_state.state == workflow.STATE_RESERVED:
            event_class = events.BookingReservedToOrderedEvent
        _set_state(
            order_state, workflow.STATE_FINISHED, event_class=event_class
        )  # noqa

    elif transition == workflow.STATE_TRANSITION_CANCEL:
        _set_state(
            order_state,
            workflow.STATE_CANCELLED,
            event_class=events.BookingCancelledEvent,
        )

    else:
        raise ValueError(u"Invalid transition: %s" % transition)
