# -*- coding: utf-8 -*-

###############################################################################
# en
###############################################################################

SUBJECT_EN= u'Order received.'

BODY_EN = """
Date: %(date)s

Ordernumber: %(orderid)s

Personal Data:
Name: %(personal_data.name)s %(personal_data.surname)s
Company: %(personal_data.company)s
Phone: %(personal_data.phone)s

Address:
Street: %(billing_address.street)s
ZIP: %(billing_address.zip)s
City: %(billing_address.city)s
Country: %(billing_address.country)s
%(delivery_address)s
Comment:
%(order_comment.comment)s

Ordered items:
%(item_listing)s
"""

DELIVERY_ADDRESS_EN = """
Delivery Address:
Name: %(delivery_address.name)s %(delivery_address.surname)s
Company: %(delivery_address.company)s
Street: %(delivery_address.street)s
ZIP: %(delivery_address.zip)s
City: %(delivery_address.city)s
Country: %(delivery_address.country)s
"""

###############################################################################
# de
###############################################################################

SUBJECT_DE= u'Order received.'

BODY_DE = """
Datum: %(date)s

Bestellnummer: %(orderid)s

Persönliche Angaben:
Name: %(personal_data.name)s %(personal_data.surname)s
Firma: %(personal_data.company)s
Telefon: %(personal_data.phone)s

Adresse:
Straße: %(billing_address.street)s
Postleitzahl: %(billing_address.zip)s
Ort: %(billing_address.city)s
Land: %(billing_address.country)s
%(delivery_address)s
Kommentar:
%(order_comment.comment)s

Bestellte Artikel:
%(item_listing)s
"""

DELIVERY_ADDRESS_DE = """
Lieferadresse:
Name: %(delivery_address.name)s %(delivery_address.surname)s
Firma: %(delivery_address.company)s
Straße: %(delivery_address.street)s
Postleitzahl: %(delivery_address.zip)s
Ort: %(delivery_address.city)s
Land: %(delivery_address.country)s
"""

###############################################################################
# language templates
###############################################################################

TEMPLATES = {
    'en': {
        'subject': SUBJECT_EN,
        'body': BODY_EN,
        'delivery_address': DELIVERY_ADDRESS_EN},
    'de': {
        'subject': SUBJECT_DE,
        'body': BODY_DE,
        'delivery_address': DELIVERY_ADDRESS_DE}}


def get_templates(context):
    lang = context.restrictedTraverse('@@plone_portal_state').language()
    return TEMPLATES.get(lang, TEMPLATES['en'])
