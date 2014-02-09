# -*- coding: utf-8 -*-
from BTrees import OOBTree
from zope.interface import implementer
from .interfaces import IDynamicMailTemplateLibrary

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

RESERVATION_SUBJECT_NO = u'Bestilling %s mottatt.'

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


class DynamicMailTemplate(object):
    """Dynamic Mail Template based on str.format
    """

    def __init__(self, required=[], defaults={}):
        """Initialize a new template

        required
            a list of keys which are required in the data to be rendered.
            all other values are taken from defaults if not provided.

        defaults
            a complete set of values for the template. used for validation,
            so it has to include all required as well.
        """
        for key in required:
            if key in defaults:
                continue
            raise ValueError(
                'All required must be in defaults too, missing: '
                '{0}'.format(key)
            )
        self.required = required
        self.defaults = defaults

    def validate(self, template):
        """validates if the template can be rendered.

        uses default values to achieve this

        template
            a unicode string meant to be rendered using python string format
            method

        """
        assert isinstance(template, unicode), 'template must be unicode'
        try:
            self(template, self.defaults)
        except KeyError, e:
            return False, u'Variable "{0}" is not available.'.format(e.message)
        except Exception, e:
            return False, e.message
        return True, ''

    def __call__(self, template, data):
        """render template with data"""
        assert isinstance(template, unicode), 'template must be unicode'
        for key in self.required:
            if key not in data:
                raise KeyError('Required key {0} is missing.'.format(key))
        return template.format(**data)


DYNAMIC_MAIL_LIBRARY_KEY = "bda.plone.order.dynamic_mail_lib"

@implementer(IDynamicMailTemplateLibrary)
class DynamicMailTemplateLibraryAquierer(object):

    def __init__(self, context):
        self.context = context

    @property
    def _parent(self):
        if not hasattr(self.context, __parent__):
            return None
        dmt_lib = queryAdapter(
            self.context.__parent__,
            IDynamicMailTemplateLibrary
        )
        return dmt_lib

    def keys(self):
        parent = self._parent
        if parent is None:
            return []
        return parent.keys()

    def __getitem__(self, name):
        parent = self._parent
        if parent is not None:
            return parent[name]
        raise KeyError('Can not aquire key %s' % name)

    def __setitem__(name, template):
        raise NotImplementedError('do not set on parent (permissions')

    def __delitem__(name):
        raise NotImplementedError('do not delete on parent (permissions')


@implementer(IDynamicMailTemplateLibrary)
class DynamicMailTemplateLibraryStorage(DynamicMailTemplateLibraryAquierer):

    @property
    def _storage(self):
        annotations = IAnnotations(self.context)
        if DYNAMIC_MAIL_LIBRARY_KEY not in  annotations:
            annotations[DYNAMIC_MAIL_LIBRARY_KEY] = OOBTree()
        return annotations[DYNAMIC_MAIL_LIBRARY_KEY]

    def keys(self):
        result = [_ for _ in self._storage.keys()]
        parent_keys = super(DynamicMailTemplateLibraryStorage, self).keys()
        for key in parent_keys:
            if key not in result:  # child wins
                result.append(key)
        return result

    def __getitem__(self, name):
        try:
            return self._storage[name]
        except KeyError:
            return super(DynamicMailTemplateLibraryStorage,
                         self).__getitem__(name)

    def __setitem__(name, template):
        self._storage[name] = template

    def __delitem__(name):
        del self._storage[name]

