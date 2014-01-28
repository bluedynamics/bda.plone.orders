from bda.plone.orders.common import get_all_vendors
from plone.uuid.interfaces import IUUID


def all_vendors_vocab():
    """Vocabulary for all vendor areas by uuid.
    """
    all_vendors = get_all_vendors()
    vocab = [(IUUID(it), it.Title()) for it in all_vendors]
    return vocab
