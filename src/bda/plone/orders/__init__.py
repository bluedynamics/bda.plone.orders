# -*- coding: utf-8 -*-
from Products.CMFPlone.utils import safe_unicode
from zope.i18nmessageid import MessageFactory

import gettext
import pycountry
import six
import unicodedata


message_factory = MessageFactory('bda.plone.orders')


def safe_encode(string):
    """Safely unicode objects to UTF-8. If it's a binary string, just return
    it.
    """
    if isinstance(string, six.string_types):
        return safe_unicode(string).encode('utf-8')
    return string


def safe_filename(value):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.

    Ideas from:
    https://github.com/django/django/blob/master/django/utils/text.py
    """
    value = safe_unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    return value.replace(' ', '-').strip()


def get_country_name(country_code, lang='en'):
    """Return the translated country name for a given pycountry country code.
    """

    country_name = pycountry.countries.get(numeric=country_code).name
    trans = gettext.translation('iso3166', pycountry.LOCALES_DIR, languages=['de'])
    return safe_unicode(trans.gettext(country_name))
