from zope.i18nmessageid import MessageFactory
message_factory = MessageFactory('bda.plone.orders')


def safe_encode(string):
    """Safely unicode objects to UTF-8. If it's a binary string, just return
    it.
    """
    if isinstance(string, unicode):
        string = string.encode('utf-8')
    return string
