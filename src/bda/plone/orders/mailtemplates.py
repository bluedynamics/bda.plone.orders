# -*- coding: utf-8 -*-

###############################################################################
# en
###############################################################################

SUBJECT_EN = u'Order %s received.'

BODY_EN = """
Date: %(date)s

Thank you for your order:

Ordernumber: %(ordernumber)s

Personal Data:
Name: %(personal_data.firstname)s %(personal_data.lastname)s
Company: %(personal_data.company)s
Phone: %(personal_data.phone)s
Email: %(personal_data.email)s

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
Name: %(delivery_address.firstname)s %(delivery_address.lastname)s
Company: %(delivery_address.company)s
Street: %(delivery_address.street)s
ZIP: %(delivery_address.zip)s
City: %(delivery_address.city)s
Country: %(delivery_address.country)s
"""

###############################################################################
# de
###############################################################################

SUBJECT_DE = u'Bestellung %s erhalten.'

BODY_DE = """
Datum: %(date)s

Besten Dank für Ihre Bestellung:

Bestellnummer: %(ordernumber)s

Persönliche Angaben:
Name: %(personal_data.firstname)s %(personal_data.lastname)s
Firma: %(personal_data.company)s
Telefon: %(personal_data.phone)s
E-Mail: %(personal_data.email)s

Adresse:
Strasse: %(billing_address.street)s
Postleitzahl: %(billing_address.zip)s
Ort: %(billing_address.city)s
Land: %(billing_address.country)s
%(delivery_address)s
Kommentar:
%(order_comment.comment)s

Bestellte Artikel:
%(item_listing)s

Total: %(order_total)s
"""

DELIVERY_ADDRESS_DE = """
Lieferadresse:
Name: %(delivery_address.firstname)s %(delivery_address.lastname)s
Firma: %(delivery_address.company)s
Strasse: %(delivery_address.street)s
Postleitzahl: %(delivery_address.zip)s
Ort: %(delivery_address.city)s
Land: %(delivery_address.country)s
"""

###############################################################################
# fr
###############################################################################

SUBJECT_FR = u'votre commande %s.'

BODY_FR = """
Date: %(date)s

Nous vous remercions pour votre commande :

No. de commande: %(ordernumber)s

Données personnelles:
Nom: %(personal_data.firstname)s %(personal_data.lastname)s
Entreprise: %(personal_data.company)s
Téléphone: %(personal_data.phone)s
E-Mail: %(personal_data.email)s

Adresse:
Rue: %(billing_address.street)s
No. Postal: %(billing_address.zip)s
Localité: %(billing_address.city)s
Pays: %(billing_address.country)s
%(delivery_address)s
Commentaires:
%(order_comment.comment)s

Produit commandé:
%(item_listing)s

Total: %(order_total)s
"""

DELIVERY_ADDRESS_FR = """
Adresse de livraison:
Nom: %(delivery_address.firstname)s %(delivery_address.lastname)s
Entreprise: %(delivery_address.company)s
Rue: %(delivery_address.street)s
No. Postal: %(delivery_address.zip)s
Localité: %(delivery_address.city)s
Pays: %(delivery_address.country)s
"""

###############################################################################
# it
###############################################################################

SUBJECT_IT = u'votre commande %s.'

BODY_IT = """
Date: %(date)s

Nous vous remercions pour votre commande :

No. de commande: %(ordernumber)s

Données personnelles:
Nom: %(personal_data.firstname)s %(personal_data.lastname)s
Entreprise: %(personal_data.company)s
Téléphone: %(personal_data.phone)s
E-Mail: %(personal_data.email)s

Adresse:
Rue: %(billing_address.street)s
No. Postal: %(billing_address.zip)s
Localité: %(billing_address.city)s
Pays: %(billing_address.country)s
%(delivery_address)s
Commentaires:
%(order_comment.comment)s

Produit commandé:
%(item_listing)s

Total: %(order_total)s
"""

DELIVERY_ADDRESS_IT = """
Lieferadresse:
Nom: %(delivery_address.firstname)s %(delivery_address.lastname)s
Entreprise: %(delivery_address.company)s
Rue: %(delivery_address.street)s
No. Postal: %(delivery_address.zip)s
Localité: %(delivery_address.city)s
Pays: %(delivery_address.country)s
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
        'delivery_address': DELIVERY_ADDRESS_DE},
    'fr': {
        'subject': SUBJECT_FR,
        'body': BODY_FR,
        'delivery_address': DELIVERY_ADDRESS_FR},
    'it': {
        'subject': SUBJECT_IT,
        'body': BODY_IT,
        'delivery_address': DELIVERY_ADDRESS_IT}
}

def get_templates(context):
    lang = context.restrictedTraverse('@@plone_portal_state').language()
    return TEMPLATES.get(lang, TEMPLATES['en'])
