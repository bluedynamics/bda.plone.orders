from Products.Five import BrowserView
from bda.plone.ajax import AjaxMessage
from bda.plone.ajax import AjaxOverlay
from bda.plone.ajax import ajax_continue
from bda.plone.ajax import ajax_form_fiddle
from bda.plone.orders import message_factory as _
from node.utils import UNSET
from yafowil.base import ExtractionError
from yafowil.plone.form import YAMLForm


class MailtemplatesForm(YAMLForm):
    """Form to edit all the mailtemplates
    """
    form_template = 'bda.plone.orders.browser:forms/mailtemplates.yaml'
    message_factory = _

    def value_tpl(self, widget, data):
        return UNSET

    def validate_tpl(self, widget, data):
        raise ExtractionError('fooo')

    def form_action(self, widget, data):
        return '%s/@@mailtemplates' % self.context.absolute_url()

    def save(self, widget, data):
        pass

    def next(self, request):
        return True
