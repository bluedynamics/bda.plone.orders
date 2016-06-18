# -*- coding: utf-8 -*-
from Products.CMFPlone.utils import safe_unicode
from zope.i18nmessageid import MessageFactory
message_factory = MessageFactory('bda.plone.orders')


def safe_encode(string):
    """Safely unicode objects to UTF-8. If it's a binary string, just return
    it.
    """
    return safe_unicode(string).encode('utf-8')
