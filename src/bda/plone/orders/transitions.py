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

    def _set_state(data, state_value, state_attr='state',
                   event_class=None, event_emit_on_last=False):
        #
        #                             Case BookingData
        #                    Case OrderData    |
        # BookingData or OrderData    |        |
        #                   V         V        V
        bookings = getattr(data, 'bookings', [data])
        bookings = list(bookings)  # make list out of generator to have a len
        bookings_len = len(bookings)
        for cnt, booking_data in enumerate(bookings):

            if not isinstance(booking_data, BookingData):
                # Case OrderData
                # It's a booking record from iterating over ``bookings`` in
                # OrderData. We have to factorize a BookingData object now.
                booking_data = BookingData(
                    context=context,
                    booking=booking_data
                )

            # Set state. This includes updates via it's setter method (E.g.
            # OrderData state and item_stock).
            setattr(booking_data, state_attr, state_value)

            # Optionally send out event.
            # May include sending out a notification mail.
            if event_class and (
                cnt == bookings_len - 1 or  # event_emit_on_last
                not event_emit_on_last      # or emit always
            ):
                booking_attrs = dict(booking_data.booking.attrs.items())
                event = event_class(
                    context=context,
                    request=request,
                    order_uid=booking_attrs['order_uid'],
                    booking_attrs=booking_attrs,
                )
                notify(event)

    if transition == interfaces.SALARIED_TRANSITION_SALARIED:
        _set_state(order_state, interfaces.SALARIED_YES, 'salaried')

    elif transition == interfaces.SALARIED_TRANSITION_OUTSTANDING:
        _set_state(order_state, interfaces.SALARIED_NO, 'salaried')

    elif transition == interfaces.STATE_TRANSITION_RENEW:
        _set_state(
            order_state,
            interfaces.STATE_NEW,
            event_class=events.OrderSuccessfulEvent,
            event_emit_on_last=True
        )

    elif transition == interfaces.STATE_TRANSITION_PROCESS:
        event_class = None
        if order_state.state == interfaces.STATE_RESERVED:
            event_class = events.BookingReservedToOrderedEvent
        _set_state(order_state, interfaces.STATE_PROCESSING, event_class=event_class)  # noqa

    elif transition == interfaces.STATE_TRANSITION_FINISH:
        event_class = None
        if order_state.state == interfaces.STATE_RESERVED:
            event_class = events.BookingReservedToOrderedEvent
        _set_state(order_state, interfaces.STATE_FINISHED, event_class=event_class)  # noqa

    elif transition == interfaces.STATE_TRANSITION_CANCEL:
        _set_state(
            order_state,
            interfaces.STATE_CANCELLED,
            event_class=events.BookingCancelledEvent
        )

    else:
        raise ValueError(u"Invalid transition: %s" % transition)
