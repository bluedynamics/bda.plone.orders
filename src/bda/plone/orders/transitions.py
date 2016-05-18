# -*- coding: utf-8 -*-
from bda.plone.orders import interfaces


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


def do_transition_for(order_state, transition, event=False):
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
        order_state.state = interfaces.STATE_CANCELLED
    else:
        raise ValueError(u"Invalid transition: %s" % transition)
