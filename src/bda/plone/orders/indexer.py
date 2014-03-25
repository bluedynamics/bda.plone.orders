from zope.interface import Interface
from plone.indexer import indexer
import plone.api


@indexer(Interface)
def customer_role(obj):
    # read users and groups having customer role directly on context, not
    # inherited! groups gets prefixed with ``group:``
    # XXX

    # TODO: seems not to be called on reindexObject
    users = obj.users_with_local_role('Customer')  # get non-aquired roles
    ret = [plone.api.group.get(it) and 'group:%s' or it for it in users]
    return ret
