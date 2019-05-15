# -*- coding: utf-8 -*-
from decimal import Decimal
from node.utils import Unset
from plone.restapi.interfaces import IJsonCompatible
from plone.restapi.serializer.converters import json_compatible
from uuid import UUID
from zope.component import adapter
from zope.interface import implementer


def json_compatible_dict(value):
    result = value.__class__()
    for key, entry in value.items():
        result[key] = json_compatible(entry)
    return result


@adapter(Unset)
@implementer(IJsonCompatible)
def unset_converter(value):
    return "<UNSET>"


@adapter(UUID)
@implementer(IJsonCompatible)
def uuid_converter(value):
    return str(value)


@adapter(Decimal)
@implementer(IJsonCompatible)
def decimal_converter(value):
    return str(value)
