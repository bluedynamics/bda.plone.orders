# -*- coding: utf-8 -*-

###############################################################################
# en
###############################################################################

ORDER_SUBJECT_EN = u'Order %s received.'

RESERVATION_SUBJECT_EN = u'Reservation %s received.'

ORDER_BODY_EN = """
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

RESERVATION_BODY_EN = """
Date: %(date)s

Thank you for your reservation:

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

ORDER_SUBJECT_DE = u'Bestellung %s erhalten.'

RESERVATION_SUBJECT_DE = u'Reservierung %s erhalten.'

ORDER_BODY_DE = """
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

RESERVATION_BODY_DE = """
Datum: %(date)s

Besten Dank für Ihre Reservierung:

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

ORDER_SUBJECT_FR = u'votre commande %s.'

RESERVATION_SUBJECT_FR = u'votre réservation %s.'

ORDER_BODY_FR = """
Date: %(date)s

Nous vous remercions pour votre commande:

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

RESERVATION_BODY_FR = """
Date: %(date)s

Nous vous remercions pour votre réservation:

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

ORDER_SUBJECT_IT = u'Il tuo ordine %s.'

RESERVATION_SUBJECT_IT = u'Il tuo prenotazione %s.'

ORDER_BODY_IT = """
Data: %(date)s

Grazie per l'ordine effettuato:

Numero d'ordine: %(ordernumber)s

Dati personali:
Nome: %(personal_data.firstname)s %(personal_data.lastname)s
Ditta: %(personal_data.company)s
Telefono: %(personal_data.phone)s

Indirizzo:
Via: %(billing_address.street)s
CAP: %(billing_address.zip)s
Città: %(billing_address.city)s
Nazione: %(billing_address.country)s
%(delivery_address)s
Commento:
%(order_comment.comment)s

Articolo ordinato:
%(item_listing)s

Totale: %(order_total)s
"""

RESERVATION_BODY_IT = """
Data: %(date)s

Grazie per l'prenotazione effettuato:

Numero d'ordine: %(ordernumber)s

Dati personali:
Nome: %(personal_data.firstname)s %(personal_data.lastname)s
Ditta: %(personal_data.company)s
Telefono: %(personal_data.phone)s

Indirizzo:
Via: %(billing_address.street)s
CAP: %(billing_address.zip)s
Città: %(billing_address.city)s
Nazione: %(billing_address.country)s
%(delivery_address)s
Commento:
%(order_comment.comment)s

Articolo ordinato:
%(item_listing)s

Totale: %(order_total)s
"""

DELIVERY_ADDRESS_IT = """
Indirizzo di spedizione:
Nome: %(delivery_address.firstname)s %(delivery_address.lastname)s
Ditta: %(delivery_address.company)s
Via: %(delivery_address.street)s
CAP: %(delivery_address.zip)s
Città: %(delivery_address.city)s
Nazione: %(delivery_address.country)s
"""

###############################################################################
# no
###############################################################################

ORDER_SUBJECT_NO = u'Bestilling %s mottatt.'

RESERVATION_SUBJECT_NO = u'Reservasjon %s motttt.'

ORDER_BODY_NO = """
Dato: %(date)s

Takk for din bestilling:

Ordernummer: %(ordernumber)s

Personlig info:
Navn: %(personal_data.firstname)s %(personal_data.lastname)s
Firma: %(personal_data.company)s
Telefon: %(personal_data.phone)s
Epost: %(personal_data.email)s

Adr:
Gate/Vei: %(billing_address.street)s
Postnr.: %(billing_address.zip)s
Poststed: %(billing_address.city)s
Land: %(billing_address.country)s
%(delivery_address)s
Kommentar:
%(order_comment.comment)s

Bestilte produkter:
%(item_listing)s
"""

RESERVATION_BODY_NO = """
Dato: %(date)s

Takk for din reservasjon:

Ordernummer: %(ordernumber)s

Personlig info:
Navn: %(personal_data.firstname)s %(personal_data.lastname)s
Firma: %(personal_data.company)s
Telefon: %(personal_data.phone)s
Epost: %(personal_data.email)s

Adr:
Gate/Vei: %(billing_address.street)s
Postnr.: %(billing_address.zip)s
Poststed: %(billing_address.city)s
Land: %(billing_address.country)s
%(delivery_address)s
Kommentar:
%(order_comment.comment)s

Bestilte produkter:
%(item_listing)s
"""

DELIVERY_ADDRESS_NO = """
Leveringsadr.:
Navn: %(delivery_address.firstname)s %(delivery_address.lastname)s
Firma: %(delivery_address.company)s
gate/Vei: %(delivery_address.street)s
Postnr.: %(delivery_address.zip)s
Poststed: %(delivery_address.city)s
Land: %(delivery_address.country)s
"""


###############################################################################
# language templates
###############################################################################

ORDER_TEMPLATES = {
    'en': {
        'subject': ORDER_SUBJECT_EN,
        'body': ORDER_BODY_EN,
        'delivery_address': DELIVERY_ADDRESS_EN},
    'de': {
        'subject': ORDER_SUBJECT_DE,
        'body': ORDER_BODY_DE,
        'delivery_address': DELIVERY_ADDRESS_DE},
    'fr': {
        'subject': ORDER_SUBJECT_FR,
        'body': ORDER_BODY_FR,
        'delivery_address': DELIVERY_ADDRESS_FR},
    'it': {
        'subject': ORDER_SUBJECT_IT,
        'body': ORDER_BODY_IT,
        'delivery_address': DELIVERY_ADDRESS_IT},
    'no': {
        'subject': ORDER_SUBJECT_NO,
        'body': ORDER_BODY_NO,
        'delivery_address': DELIVERY_ADDRESS_NO}
}

RESERVATION_TEMPLATES = {
    'en': {
        'subject': RESERVATION_SUBJECT_EN,
        'body': RESERVATION_BODY_EN,
        'delivery_address': DELIVERY_ADDRESS_EN},
    'de': {
        'subject': RESERVATION_SUBJECT_DE,
        'body': RESERVATION_BODY_DE,
        'delivery_address': DELIVERY_ADDRESS_DE},
    'fr': {
        'subject': RESERVATION_SUBJECT_FR,
        'body': RESERVATION_BODY_FR,
        'delivery_address': DELIVERY_ADDRESS_FR},
    'it': {
        'subject': RESERVATION_SUBJECT_IT,
        'body': RESERVATION_BODY_IT,
        'delivery_address': DELIVERY_ADDRESS_IT},
    'no': {
        'subject': RESERVATION_SUBJECT_NO,
        'body': RESERVATION_BODY_NO,
        'delivery_address': DELIVERY_ADDRESS_NO}
}


def get_order_templates(context):
    lang = context.restrictedTraverse('@@plone_portal_state').language()
    return ORDER_TEMPLATES.get(lang, ORDER_TEMPLATES['en'])


def get_reservation_templates(context):
    lang = context.restrictedTraverse('@@plone_portal_state').language()
    return RESERVATION_TEMPLATES.get(lang, RESERVATION_TEMPLATES['en'])
