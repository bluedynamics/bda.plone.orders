# -*- coding: utf-8 -*-
from bda.plone.orders.common import get_order
from repoze.catalog.catalog import Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.text import CatalogTextIndex
from repoze.catalog.query import Eq
from souper.interfaces import ICatalogFactory
from souper.soup import NodeAttributeIndexer
from souper.soup import NodeTextIndexer
from souper.soup import Record
from souper.soup import get_soup
from zope.interface import implementer
import random
import uuid
from six.moves import range


def get_contacts_soup(context):
    return get_soup('bda_plone_orders_contacts', context)


class ContactAttributeIndexer(NodeAttributeIndexer):
    """souper indexer for export contact attributes.
    """

    def __call__(self, context, default):
        if self.attr in context.attrs:
            return context.attrs[self.attr].lower()
        return default


@implementer(ICatalogFactory)
class ContactsCatalogFactory(object):

    def __call__(self, context=None):
        catalog = Catalog()
        uid_indexer = NodeAttributeIndexer('uid')
        catalog[u'uid'] = CatalogFieldIndex(uid_indexer)
        email_indexer = NodeAttributeIndexer('personal_data.email')
        catalog[u'email'] = CatalogFieldIndex(email_indexer)
        cid_indexer = NodeAttributeIndexer('cid')
        catalog[u'cid'] = CatalogFieldIndex(cid_indexer)
        firstname_indexer = ContactAttributeIndexer('personal_data.firstname')
        catalog[u'firstname'] = CatalogFieldIndex(firstname_indexer)
        lastname_indexer = ContactAttributeIndexer('personal_data.lastname')
        catalog[u'lastname'] = CatalogFieldIndex(lastname_indexer)
        zip_indexer = ContactAttributeIndexer('billing_address.zip')
        catalog[u'zip'] = CatalogFieldIndex(zip_indexer)
        street_indexer = ContactAttributeIndexer('billing_address.street')
        catalog[u'street'] = CatalogFieldIndex(street_indexer)
        search_attributes = ['personal_data.email',
                             'personal_data.firstname',
                             'personal_data.lastname'
                             ]
        text_indexer = NodeTextIndexer(search_attributes)
        catalog[u'text'] = CatalogTextIndex(text_indexer)
        return catalog


# attributes for extracting contacts
CONTACT_ATTRIBUTES = [
    'personal_data.company',
    'personal_data.email',
    'personal_data.gender',
    'personal_data.firstname',
    'personal_data.phone',
    'personal_data.lastname',
    'billing_address.city',
    'billing_address.country',
    'billing_address.street',
    'billing_address.zip',
    'delivery_address.city',
    'delivery_address.company',
    'delivery_address.country',
    'delivery_address.firstname',
    'delivery_address.street',
    'delivery_address.lastname',
    'delivery_address.zip',
]


def extract_contact(order):
    """Extract export contact from order by ``CONTACT_ATTRIBUTE_MAP`` keys.
    """
    contact = dict()
    for attr in CONTACT_ATTRIBUTES:
        contact[attr] = order.attrs.get(attr, u'').strip()
    return contact


# maximum attempts for creating a new contact id before failure
MAX_NEW_CONTACT_ID_ATTEMPTS = 10


def next_contact_id(soup):
    """Create a unique contact id.
    """
    next_id = None
    attempts = MAX_NEW_CONTACT_ID_ATTEMPTS
    for i in range(attempts):
        next_id = random.randint(0, 1000000)
        res = [r for r in soup.query(Eq('cid', next_id))]
        if not res:
            return next_id
    msg = u'Unable to create unique contact id after %i attempts.' % attempts
    raise ValueError(msg)


def lookup_contact(context, contact):
    """Lookup existing contact from soup by given contact or add to soup
    if inexistent.
    """
    soup = get_contacts_soup(context)
    query = (
        Eq('firstname', contact['personal_data.firstname'].lower()) &
        Eq('lastname', contact['personal_data.lastname'].lower()) &
        Eq('zip', contact['billing_address.zip'].lower()) &
        Eq('street', contact['billing_address.street'].lower())
    )
    res = soup.query(query)
    record = None
    for rec in res:
        record = rec
        break
    if not record:
        record = Record()
        record.attrs['uid'] = uuid.uuid4()
        record.attrs['cid'] = next_contact_id(soup)
        record.attrs.update(list(contact.items()))
        soup.add(record)
    else:
        record.attrs.update(list(contact.items()))
        soup.reindex([record])
    return record


def save_contact(event):
    """``bda.plone.checkout.interfaces.ICheckoutDone`` subscriber for storing
    order contact to soup.
    """
    order = get_order(event.context, event.uid)
    lookup_contact(event.context, extract_contact(order))
