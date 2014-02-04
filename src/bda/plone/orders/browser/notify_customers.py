from Products.Five import BrowserView
from node.utils import UNSET
from yafowil.plone.form import YAMLForm
from bda.plone.ajax import ajax_continue
from bda.plone.ajax import AjaxOverlay
from bda.plone.ajax import AjaxMessage
from .. import message_factory as _


class NotifyCustomers(YAMLForm):
    """Notify customers form.
    """
    form_template = 'bda.plone.orders.browser:forms/notify_customers.yaml'
    message_factory = _

    def form_action(self, widget, data):
        return '%s/ajaxform?form_name=notify_customers' % \
            self.context.absolute_url()

    def selector_value(self, widget, data):
        return 'form[id=form-notify_customers]'

    def mode_value(self, widget, data):
        return 'replace'

    def template_value(self, widget, data):
        return UNSET

    def template_vocabulary(self, widget, data):
        return [
            ('-', _('no_template_selected', default=u'No template selected')),
        ]

    def text_value(self, widget, data):
        return UNSET

    def send(self, widget, data):
        print 'send'

    def send_success(self, request):
        message = _('customers_notified_success',
                    default=u'Mail to customers sent')
        continuation = [
            AjaxOverlay(close=True),
            AjaxMessage(message, 'info', None)
        ]
        ajax_continue(self.request, continuation)
        return True
