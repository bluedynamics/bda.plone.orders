# -*- coding: utf-8 -*-
from bda.plone.orders import message_factory as _
from bda.plone.orders.interfaces import IDynamicMailTemplateLibraryStorage
from bda.plone.orders.mailtemplates import DEFAULT_TEMPLATE_ATTRS
from bda.plone.orders.mailtemplates import DynamicMailTemplate
from bda.plone.orders.mailtemplates import REQUIRED_TEMPLATE_ATTRS
from Products.Five import BrowserView
from yafowil.base import ExtractionError
from yafowil.plone.form import YAMLForm

TEMPLATE = DynamicMailTemplate(
    required=REQUIRED_TEMPLATE_ATTRS,
    defaults=DEFAULT_TEMPLATE_ATTRS
)


class MailtemplatesView(BrowserView):

    def default_attrs(self):
        items = []
        for key in sorted(DEFAULT_TEMPLATE_ATTRS.keys()):
            items.append({
                'placeholder': key.replace('.', '_'),
                'example': DEFAULT_TEMPLATE_ATTRS[key],
            })
        return items

    def rendered(self):
        tpllib = IDynamicMailTemplateLibraryStorage(self.context)
        items = []
        for key in tpllib.direct_keys():
            preview = TEMPLATE(
                tpllib[key].decode('utf8'),
                DEFAULT_TEMPLATE_ATTRS
            )
            items.append({
                'title': key,
                'preview': preview
            })
        return items


class MailtemplatesForm(YAMLForm):
    """Form to edit all the mailtemplates
    """
    form_template = 'bda.plone.orders.browser:forms/mailtemplates.yaml'
    message_factory = _

    def value_tpl(self, widget, data):
        tpllib = IDynamicMailTemplateLibraryStorage(self.context)
        value = []
        for key in tpllib.direct_keys():
            value.append({
                'title': key,
                'template': tpllib[key]
            })
        return value

    def validate_tpl(self, widget, data):
        state, msg = TEMPLATE.validate(data.extracted.decode('utf8'))
        if not state:
            raise ExtractionError(msg)
        return data.extracted

    def form_action(self, widget, data):
        return '%s/@@mailtemplates' % self.context.absolute_url()

    def save(self, widget, data):
        tpllib = IDynamicMailTemplateLibraryStorage(self.context)
        newkeys = []
        for record in data.extracted['array']:
            newkeys.append(record['title'])
            tpllib[record['title']] = record['template']
        for key in tpllib.direct_keys():
            if key not in newkeys:
                del tpllib[key]
        self.request.response.redirect(self.form_action(widget, data))

    def next(self, request):
        return True
