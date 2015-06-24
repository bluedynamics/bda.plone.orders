# -*- coding: utf-8 -*-
from bda.plone.orders import interfaces
from souper.soup import get_soup


def transitions_of_main_state(state):
    """list of transitions for a given orders or bookings main state
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
    """list of transitions for a given orders or bookings salaried state
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


def do_transition_for_booking(booking, transition, order_data, event=False):
    """do any transition for a given single booking

    this mixes main state and salaried!
    """
    # XXX: currently we need to delete attribute before setting to a new
    #      value in order to persist change. fix in appropriate place.
    if transition == interfaces.SALARIED_TRANSITION_SALARIED:
        del booking.attrs['salaried']
        booking.attrs['salaried'] = interfaces.SALARIED_YES
    elif transition == interfaces.SALARIED_TRANSITION_OUTSTANDING:
        del booking.attrs['salaried']
        booking.attrs['salaried'] = interfaces.SALARIED_NO
    elif transition == interfaces.STATE_TRANSITION_RENEW:
        del booking.attrs['state']
        booking.attrs['state'] = interfaces.STATE_NEW
        # fix stock item available
        order_data.decrease_stock([booking])
    elif transition == interfaces.STATE_TRANSITION_PROCESS:
        del booking.attrs['state']
        booking.attrs['state'] = interfaces.STATE_PROCESSING
    elif transition == interfaces.STATE_TRANSITION_FINISH:
        del booking.attrs['state']
        booking.attrs['state'] = interfaces.STATE_FINISHED
    elif transition == interfaces.STATE_TRANSITION_CANCEL:
        del booking.attrs['state']
        booking.attrs['state'] = interfaces.STATE_CANCELLED
        # fix stock item available
        order_data.increase_stock([booking])
    else:
        raise ValueError(u"invalid transition: %s" % transition)
    bookings_soup = get_soup('bda_plone_orders_bookings', order_data.context)
    bookings_soup.reindex(records=[booking])
