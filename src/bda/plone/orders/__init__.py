# -*- coding: utf-8 -*-
from Products.CMFPlone.utils import safe_unicode
from zope.i18nmessageid import MessageFactory

import gettext
import pycountry


message_factory = MessageFactory('bda.plone.orders')


def safe_encode(string):
    """Safely unicode objects to UTF-8. If it's a binary string, just return
    it.
    """
    return safe_unicode(string).encode('utf-8')


def get_country_name(country_code, lang='en'):
    """Return the translated country name for a given pycountry country code.
    """

    country_name = pycountry.countries.get(numeric=country_code).name
    trans = gettext.translation(
        'iso3166', pycountry.LOCALES_DIR, languages=['de']
    )
    return safe_unicode(trans.gettext(country_name))
