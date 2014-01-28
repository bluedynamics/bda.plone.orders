from bda.plone.orders.common import get_all_vendors
from plone.uuid.interfaces import IUUID
from zope.interface import directlyProvides
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


def AllVendorAreas(context, query=None):
    """Vocabulary for all vendor areas by uuid.
    """
    all_vendors = get_all_vendors()
    tz_list = [SimpleTerm(value=IUUID(it), title=it.Title())
               for it in all_vendors
               if query is None or query.lower() in it.lower()]
    return SimpleVocabulary(tz_list)
directlyProvides(AllVendorAreas, IVocabularyFactory)
