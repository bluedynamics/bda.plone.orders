from zope.interface import Interface
from plone.indexer import indexer
import plone.api


@indexer(Interface)
def customer_role(obj):
    """Index users and groups with ``Customer`` role directly on the context.
    Don't index inherited `Customer` role.  Groups are prefixed with ``group:``
    """
    users = obj.users_with_local_role('Customer')  # get non-aquired roles
    ret = [plone.api.group.get(it) and 'group:%s' % it or it for it in users]
    return ret
