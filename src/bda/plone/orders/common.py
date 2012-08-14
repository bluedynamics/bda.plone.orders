from zope.interface import implementer
from zope.component import adapts
from repoze.catalog.catalog import Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from souper.interfaces import ICatalogFactory
from souper.soup import (
    get_soup,
    Record,
    NodeAttributeIndexer,
)