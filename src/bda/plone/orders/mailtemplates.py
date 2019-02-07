# -*- coding: utf-8 -*-
from BTrees.OOBTree import OOBTree
from bda.plone.orders import interfaces as ifaces
from bda.plone.orders.interfaces import IDynamicMailTemplateLibrary
from bda.plone.orders.interfaces import IDynamicMailTemplateLibraryStorage
from zope.annotation import IAnnotations
from zope.component import queryAdapter
from zope.interface import implementer
import six


###############################################################################
# text templates
###############################################################################

# EN ##########################################################################

ORDER_SUBJECT_EN = u'Order %s received.'

ORDER_BODY_EN = u"""
Date: %(date)s

Thank you for your order:

Ordernumber: %(ordernumber)s
Order details: %(portal_url)s/@@showorder?ordernumber=%(ordernumber)s

Invoice: %(portal_url)s/@@showinvoice?ordernumber=%(ordernumber)s

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

%(order_summary)s%(global_text)s%(payment_text)s
"""

RESERVATION_SUBJECT_EN = u'Reservation %s received.'

RESERVATION_BODY_EN = u"""
Date: %(date)s

Thank you for your reservation:

Ordernumber: %(ordernumber)s
Reservation details: %(portal_url)s/@@showorder?ordernumber=%(ordernumber)s

Invoice: %(portal_url)s/@@showinvoice?ordernumber=%(ordernumber)s

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

Reserved items:
%(reserved_item_listing)s

%(order_summary)s%(global_text)s%(payment_text)s
"""

DELIVERY_ADDRESS_EN = u"""
Delivery Address:
Name: %(delivery_address.firstname)s %(delivery_address.lastname)s
Company: %(delivery_address.company)s
Street: %(delivery_address.street)s
ZIP: %(delivery_address.zip)s
City: %(delivery_address.city)s
Country: %(delivery_address.country)s
"""

CANCELLED_BOOKING_SUBJECT_EN = u"Cancelled one booking of Order %s."

CANCELLED_BOOKING_BODY_EN = u"""
Date: %(date)s

One of your bookings was cancelled.

Ordernumber: %(ordernumber)s
Cancelled item: %(booking_cancelled_title)s

Order details: %(portal_url)s/@@showorder?ordernumber=%(ordernumber)s
"""

BOOKING_RESERVED_TO_ORDERED_SUBJECT_EN = u"Reservation of %s is now available."

BOOKING_RESERVED_TO_ORDERED_BODY_EN = u"""
Date: %(date)s

Your reserved item is now available and our order is being processed.

Ordernumber: %(ordernumber)s
Booked item: %(booking_reserved_to_ordered_title)s

Order details: %(portal_url)s/@@showorder?ordernumber=%(ordernumber)s
"""

STOCK_THRESHOLD_REACHED_SUBJECT_EN = u"Order %s has products that are getting out of stock."  # noqa

STOCK_THRESHOLD_REACHED_BODY_EN = u"""
Date: %(date)s

Products getting out of stock:
%(stock_threshold_reached_text)s
"""

# DE ##########################################################################

ORDER_SUBJECT_DE = u'Bestellung %s erhalten.'

RESERVATION_SUBJECT_DE = u'Reservierung %s erhalten.'

ORDER_BODY_DE = u"""
Datum: %(date)s

Besten Dank für Ihre Bestellung:

Bestellnummer: %(ordernumber)s
Details zur Bestellung: %(portal_url)s/@@showorder?ordernumber=%(ordernumber)s

Rechnung: %(portal_url)s/@@showinvoice?ordernumber=%(ordernumber)s

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

%(order_summary)s%(global_text)s%(payment_text)s
"""

RESERVATION_BODY_DE = u"""
Datum: %(date)s

Besten Dank für Ihre Reservierung:

Bestellnummer: %(ordernumber)s
Details zur Reservierung: %(portal_url)s/@@showorder?ordernumber=%(ordernumber)s

Rechnung: %(portal_url)s/@@showinvoice?ordernumber=%(ordernumber)s

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

Reservierte Artikel:
%(reserved_item_listing)s

%(order_summary)s%(global_text)s%(payment_text)s
"""  # noqa

DELIVERY_ADDRESS_DE = u"""
Lieferadresse:
Name: %(delivery_address.firstname)s %(delivery_address.lastname)s
Firma: %(delivery_address.company)s
Strasse: %(delivery_address.street)s
Postleitzahl: %(delivery_address.zip)s
Ort: %(delivery_address.city)s
Land: %(delivery_address.country)s
"""

CANCELLED_BOOKING_SUBJECT_DE = u"Stornierung eines Artikels in Bestellung %s."

CANCELLED_BOOKING_BODY_DE = u"""
Datum: %(date)s

Eine Ihrer bestellten Artikel wurde storniert.

Bestellnummer: %(ordernumber)s
Stornierter Artikel: %(booking_cancelled_title)s

Details zur Bestellung: %(portal_url)s/@@showorder?ordernumber=%(ordernumber)s
"""

BOOKING_RESERVED_TO_ORDERED_SUBJECT_DE = u"Reservierung %s ist nun verfügbar."

BOOKING_RESERVED_TO_ORDERED_BODY_DE = u"""
Datum: %(date)s

Ihr reservierter Artikel ist verfügbar geworden und Ihre Bestellung wird nun bearbeitet.

Bestellnummer: %(ordernumber)s
Bestellter Artikel: %(booking_reserved_to_ordered_title)s

Details zur Bestellung: %(portal_url)s/@@showorder?ordernumber=%(ordernumber)s
"""  # noqa

# FR ##########################################################################

ORDER_SUBJECT_FR = u'votre commande %s.'

RESERVATION_SUBJECT_FR = u'votre réservation %s.'

ORDER_BODY_FR = u"""
Date: %(date)s

Nous vous remercions pour votre commande:

No. de commande: %(ordernumber)s
%(portal_url)s/@@showorder?ordernumber=%(ordernumber)s

Le calcul: %(portal_url)s/@@showinvoice?ordernumber=%(ordernumber)s

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

%(order_summary)s%(global_text)s%(payment_text)s
"""

RESERVATION_BODY_FR = u"""
Date: %(date)s

Nous vous remercions pour votre réservation:

No. de commande: %(ordernumber)s
%(portal_url)s/@@showorder?ordernumber=%(ordernumber)s

Le calcul: %(portal_url)s/@@showinvoice?ordernumber=%(ordernumber)s

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

Produit réservés:
%(reserved_item_listing)s

%(order_summary)s%(global_text)s%(payment_text)s
"""

DELIVERY_ADDRESS_FR = u"""
Adresse de livraison:
Nom: %(delivery_address.firstname)s %(delivery_address.lastname)s
Entreprise: %(delivery_address.company)s
Rue: %(delivery_address.street)s
No. Postal: %(delivery_address.zip)s
Localité: %(delivery_address.city)s
Pays: %(delivery_address.country)s
"""

CANCELLED_BOOKING_SUBJECT_FR = u"Cancelled one booking of Order %s."

CANCELLED_BOOKING_BODY_FR = u"""
Date: %(date)s

One of your bookings was cancelled.

Ordernumber: %(ordernumber)s
Cancelled item: %(booking_cancelled_title)s

Order details: %(portal_url)s/@@showorder?ordernumber=%(ordernumber)s
"""

# IT ##########################################################################

ORDER_SUBJECT_IT = u'Il tuo ordine %s.'

RESERVATION_SUBJECT_IT = u'Il tuo prenotazione %s.'

ORDER_BODY_IT = u"""
Data: %(date)s

Grazie per l'ordine effettuato:

Numero d'ordine: %(ordernumber)s
%(portal_url)s/@@showorder?ordernumber=%(ordernumber)s

La fattura: %(portal_url)s/@@showinvoice?ordernumber=%(ordernumber)s

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

%(order_summary)s%(global_text)s%(payment_text)s
"""

RESERVATION_BODY_IT = u"""
Data: %(date)s

Grazie per l'prenotazione effettuato:

Numero d'ordine: %(ordernumber)s
%(portal_url)s/@@showorder?ordernumber=%(ordernumber)s

La fattura: %(portal_url)s/@@showinvoice?ordernumber=%(ordernumber)s

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

Articolo riservato:
%(reserved_item_listing)s

%(order_summary)s%(global_text)s%(payment_text)s
"""

DELIVERY_ADDRESS_IT = u"""
Indirizzo di spedizione:
Nome: %(delivery_address.firstname)s %(delivery_address.lastname)s
Ditta: %(delivery_address.company)s
Via: %(delivery_address.street)s
CAP: %(delivery_address.zip)s
Città: %(delivery_address.city)s
Nazione: %(delivery_address.country)s
"""

CANCELLED_BOOKING_SUBJECT_IT = u"Cancelled one booking of Order %s."

CANCELLED_BOOKING_BODY_IT = u"""
Date: %(date)s

One of your bookings was cancelled.

Ordernumber: %(ordernumber)s
Cancelled item: %(booking_cancelled_title)s

Order details: %(portal_url)s/@@showorder?ordernumber=%(ordernumber)s
"""

# NO ##########################################################################

ORDER_SUBJECT_NO = u'Bestilling %s mottatt.'

RESERVATION_SUBJECT_NO = u'Bestilling %s mottatt.'

ORDER_BODY_NO = u"""
Dato: %(date)s

Takk for din bestilling:

Ordernummer: %(ordernumber)s
%(portal_url)s/@@showorder?ordernumber=%(ordernumber)s

Regning: %(portal_url)s/@@showinvoice?ordernumber=%(ordernumber)s

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

%(order_summary)s%(global_text)s%(payment_text)s
"""

RESERVATION_BODY_NO = u"""
Dato: %(date)s

Takk for din bestilling:

Ordernummer: %(ordernumber)s
%(portal_url)s/@@showorder?ordernumber=%(ordernumber)s

Regning: %(portal_url)s/@@showinvoice?ordernumber=%(ordernumber)s

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

Reserverte produkter:
%(reserved_item_listing)s

%(order_summary)s%(global_text)s%(payment_text)s
"""

DELIVERY_ADDRESS_NO = u"""
Leveringsadr.:
Navn: %(delivery_address.firstname)s %(delivery_address.lastname)s
Firma: %(delivery_address.company)s
gate/Vei: %(delivery_address.street)s
Postnr.: %(delivery_address.zip)s
Poststed: %(delivery_address.city)s
Land: %(delivery_address.country)s
"""

CANCELLED_BOOKING_SUBJECT_NO = u"Cancelled one booking of Order %s."

CANCELLED_BOOKING_BODY_NO = u"""
Date: %(date)s

One of your bookings was cancelled.

Ordernumber: %(ordernumber)s
Cancelled item: %(booking_cancelled_title)s

Order details: %(portal_url)s/@@showorder?ordernumber=%(ordernumber)s
"""


###############################################################################
# text template registry
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

CANCELLED_BOOKING_TEMPLATES = {
    'en': {
        'subject': CANCELLED_BOOKING_SUBJECT_EN,
        'body': CANCELLED_BOOKING_BODY_EN},
    'de': {
        'subject': CANCELLED_BOOKING_SUBJECT_DE,
        'body': CANCELLED_BOOKING_BODY_DE},
    'fr': {
        'subject': CANCELLED_BOOKING_SUBJECT_FR,
        'body': CANCELLED_BOOKING_BODY_FR},
    'it': {
        'subject': CANCELLED_BOOKING_SUBJECT_IT,
        'body': CANCELLED_BOOKING_BODY_IT},
    'no': {
        'subject': CANCELLED_BOOKING_SUBJECT_NO,
        'body': CANCELLED_BOOKING_BODY_NO}
}

BOOKING_RESERVED_TO_ORDERED_TEMPLATES = {
    'en': {
        'subject': BOOKING_RESERVED_TO_ORDERED_SUBJECT_EN,
        'body': BOOKING_RESERVED_TO_ORDERED_BODY_EN},
    'de': {
        'subject': BOOKING_RESERVED_TO_ORDERED_SUBJECT_DE,
        'body': BOOKING_RESERVED_TO_ORDERED_BODY_DE}
}

STOCK_THRESHOLD_REACHED_TEMPLATES = {
    'en': {
        'subject': STOCK_THRESHOLD_REACHED_SUBJECT_EN,
        'body': STOCK_THRESHOLD_REACHED_BODY_EN}
}


def _get_templates(context, TPL, default='en'):
    lang = context.restrictedTraverse('@@plone_portal_state').language()
    return TPL.get(lang, TPL[default])


def get_order_templates(context):
    return _get_templates(context, ORDER_TEMPLATES)


def get_reservation_templates(context):
    return _get_templates(context, RESERVATION_TEMPLATES)


def get_booking_cancelled_templates(context):
    return _get_templates(context, CANCELLED_BOOKING_TEMPLATES)


def get_booking_reserved_to_ordered_templates(context):
    return _get_templates(context, BOOKING_RESERVED_TO_ORDERED_TEMPLATES)


def get_stock_threshold_reached_templates(context):
    return _get_templates(context, STOCK_THRESHOLD_REACHED_TEMPLATES)


###############################################################################
# dynamic mail templates
###############################################################################

# list of template attributes which are required. by default, no attributes are
# required.
REQUIRED_TEMPLATE_ATTRS = list()


# dictionary with attributes valid in mail template as keys, values are used
# for template validation
DEFAULT_TEMPLATE_ATTRS = {
    'created': '14.2.2014 14:42',
    'ordernumber': '123456',
    'salaried': ifaces.SALARIED_NO,
    'state': ifaces.STATE_NEW,
    'personal_data.company': 'ACME LTD.',
    'personal_data.email': 'max.mustermann@example.com',
    'personal_data.gender': 'male',
    'personal_data.firstname': 'Max',
    'personal_data.phone': '+43 123 456 78 90',
    'personal_data.lastname': 'Mustermann',
    'billing_address.city': 'Springfield',
    'billing_address.country': 'Austria',
    'billing_address.street': 'Musterstrasse',
    'billing_address.zip': '1234',
    'order_comment.comment': 'Comment',
    'payment_selection.payment': 'six_payment',
}


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
                u'All required must be in defaults too, missing: '
                u'{0}'.format(key)
            )
        self.required = required
        self.defaults = defaults

    def normalized(self, keys=[], indict={}):
        if keys and indict:
            raise ValueError('Only one kwargs please.')
        if keys:
            result = []
            for key in keys:
                result.append(key.replace('.', '_'))
            return result
        if indict:
            result = {}
            for key, value in indict.items():
                if isinstance(value, str):
                    value = value.decode('utf-8')
                result[key.replace('.', '_')] = value
            return result
        raise ValueError('Only one kwargs please.')

    def validate(self, template):
        """validates if the template can be rendered.

        uses default values to achieve this

        template
            a unicode string meant to be rendered using python string format
            method
        """
        assert isinstance(template, six.text_type), 'template must be unicode'
        try:
            self(template, self.defaults)
        except KeyError as e:
            return False, u'Variable "{0}" is not available.'.format(e.message)
        except Exception as e:
            return False, e.message
        return True, ''

    def __call__(self, template, data):
        """render template with data
        """
        assert isinstance(template, six.text_type), 'template must be unicode'
        for key in self.required:
            if key not in data:
                raise KeyError(u'Required key {0} is missing.'.format(key))
        return template.format(**self.normalized(indict=data))


DYNAMIC_MAIL_LIBRARY_KEY = "bda.plone.order.dynamic_mail_lib"


@implementer(IDynamicMailTemplateLibrary)
class DynamicMailTemplateLibraryAquierer(object):

    def __init__(self, context):
        self.context = context

    def _parent(self):
        if not hasattr(self.context, '__parent__'):
            return None
        if self.context.__parent__:
            dmt_lib = queryAdapter(
                self.context.__parent__,
                IDynamicMailTemplateLibrary,
            )
            return dmt_lib

    def keys(self):
        parent = self._parent()
        if parent is None:
            return []
        return list(parent.keys())

    def __getitem__(self, name):
        parent = self._parent()
        if parent is not None:
            return parent[name]
        raise KeyError('Can not aquire key %s' % name)

    def __setitem__(self, name, template):
        raise NotImplementedError(
            'acquierer do not set on parent (permissions)'
        )

    def __delitem__(self, name):
        raise NotImplementedError(
            'acquierer do not delete on parent (permissions)'
        )


@implementer(IDynamicMailTemplateLibraryStorage)
class DynamicMailTemplateLibraryStorage(DynamicMailTemplateLibraryAquierer):

    @property
    def _storage(self):
        annotations = IAnnotations(self.context)
        if DYNAMIC_MAIL_LIBRARY_KEY not in annotations:
            annotations[DYNAMIC_MAIL_LIBRARY_KEY] = OOBTree()
        return annotations[DYNAMIC_MAIL_LIBRARY_KEY]

    def direct_keys(self):
        return [_ for _ in self._storage.keys()]

    def keys(self):
        result = self.direct_keys()
        parent_keys = list(super(DynamicMailTemplateLibraryStorage, self).keys())
        for key in parent_keys:
            if key not in result:  # child wins
                result.append(key)
        return result

    def __getitem__(self, name):
        try:
            return self._storage[name]
        except KeyError:
            return super(
                DynamicMailTemplateLibraryStorage,
                self
            ).__getitem__(name)

    def __setitem__(self, name, template):
        self._storage[name] = template

    def __delitem__(self, name):
        del self._storage[name]
