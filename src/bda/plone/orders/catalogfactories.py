# -*- coding: utf-8 -*-
from repoze.catalog.catalog import Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.keyword import CatalogKeywordIndex
from repoze.catalog.indexes.text import CatalogTextIndex
from souper.interfaces import ICatalogFactory
from souper.soup import NodeAttributeIndexer
from souper.soup import NodeTextIndexer
from zope.interface import implementer


@implementer(ICatalogFactory)
class BookingsCatalogFactory(object):
    def __call__(self, context=None):
        catalog = Catalog()
        email_indexer = NodeAttributeIndexer("email")
        catalog[u"email"] = CatalogFieldIndex(email_indexer)
        uid_indexer = NodeAttributeIndexer("uid")
        catalog[u"uid"] = CatalogFieldIndex(uid_indexer)
        buyable_uid_indexer = NodeAttributeIndexer("buyable_uid")
        catalog[u"buyable_uid"] = CatalogFieldIndex(buyable_uid_indexer)
        order_uid_indexer = NodeAttributeIndexer("order_uid")
        catalog[u"order_uid"] = CatalogFieldIndex(order_uid_indexer)
        vendor_uid_indexer = NodeAttributeIndexer("vendor_uid")
        catalog[u"vendor_uid"] = CatalogFieldIndex(vendor_uid_indexer)
        creator_indexer = NodeAttributeIndexer("creator")
        catalog[u"creator"] = CatalogFieldIndex(creator_indexer)
        created_indexer = NodeAttributeIndexer("created")
        catalog[u"created"] = CatalogFieldIndex(created_indexer)
        exported_indexer = NodeAttributeIndexer("exported")
        catalog[u"exported"] = CatalogFieldIndex(exported_indexer)
        title_indexer = NodeAttributeIndexer("title")
        catalog[u"title"] = CatalogFieldIndex(title_indexer)
        state_indexer = NodeAttributeIndexer("state")
        catalog[u"state"] = CatalogFieldIndex(state_indexer)
        salaried_indexer = NodeAttributeIndexer("salaried")
        catalog[u"salaried"] = CatalogFieldIndex(salaried_indexer)
        search_attributes = ["email", "title"]
        text_indexer = NodeTextIndexer(search_attributes)
        catalog[u"text"] = CatalogTextIndex(text_indexer)
        return catalog


@implementer(ICatalogFactory)
class OrdersCatalogFactory(object):
    def __call__(self, context=None):
        catalog = Catalog()
        uid_indexer = NodeAttributeIndexer("uid")
        catalog[u"uid"] = CatalogFieldIndex(uid_indexer)
        email_indexer = NodeAttributeIndexer("personal_data.email")
        catalog[u"personal_data.email"] = CatalogFieldIndex(email_indexer)
        ordernumber_indexer = NodeAttributeIndexer("ordernumber")
        catalog[u"ordernumber"] = CatalogFieldIndex(ordernumber_indexer)
        booking_uids_indexer = NodeAttributeIndexer("booking_uids")
        catalog[u"booking_uids"] = CatalogKeywordIndex(booking_uids_indexer)
        vendor_uids_indexer = NodeAttributeIndexer("vendor_uids")
        buyable_uids_indexer = NodeAttributeIndexer("buyable_uids")
        catalog[u"buyable_uids"] = CatalogKeywordIndex(buyable_uids_indexer)
        catalog[u"vendor_uids"] = CatalogKeywordIndex(vendor_uids_indexer)
        creator_indexer = NodeAttributeIndexer("creator")
        catalog[u"creator"] = CatalogFieldIndex(creator_indexer)
        created_indexer = NodeAttributeIndexer("created")
        catalog[u"created"] = CatalogFieldIndex(created_indexer)
        firstname_indexer = NodeAttributeIndexer("personal_data.firstname")
        catalog[u"personal_data.firstname"] = CatalogFieldIndex(firstname_indexer)
        lastname_indexer = NodeAttributeIndexer("personal_data.lastname")
        catalog[u"personal_data.lastname"] = CatalogFieldIndex(lastname_indexer)
        city_indexer = NodeAttributeIndexer("billing_address.city")
        catalog[u"billing_address.city"] = CatalogFieldIndex(city_indexer)
        search_attributes = [
            "personal_data.lastname",
            "personal_data.firstname",
            "personal_data.email",
            "billing_address.city",
            "ordernumber",
        ]
        text_indexer = NodeTextIndexer(search_attributes)
        catalog[u"text"] = CatalogTextIndex(text_indexer)
        # state on order only used for sorting in orders table
        state_indexer = NodeAttributeIndexer("state")
        catalog[u"state"] = CatalogFieldIndex(state_indexer)
        # salaried on order only used for sorting in orders table
        salaried_indexer = NodeAttributeIndexer("salaried")
        catalog[u"salaried"] = CatalogFieldIndex(salaried_indexer)
        return catalog
