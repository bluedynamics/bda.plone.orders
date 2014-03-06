from .mailtemplates import TEMPLATE
from Products.Five import BrowserView
from bda.plone.ajax import AjaxMessage
from bda.plone.ajax import AjaxOverlay
from bda.plone.ajax import ajax_continue
from bda.plone.ajax import ajax_form_fiddle
from bda.plone.orders import message_factory as _
from bda.plone.orders.interfaces import IDynamicMailTemplateLibrary
from node.utils import UNSET
from yafowil.base import ExtractionError
from yafowil.plone.form import YAMLBaseForm
import json

class NotifyCustomers(YAMLBaseForm):
    """Notify customers form.
    """
    form_template = 'bda.plone.orders.browser:forms/notify_customers.yaml'
    message_factory = _

    def form_action(self, widget, data):
        return '%s/ajaxform?form_name=notify_customers' % \
            self.context.absolute_url()

    def template_value(self, widget, data):
        if data.extracted and data.extracted['template'] != '-':
            tpllib = IDynamicMailTemplateLibrary(self.context)
            try:
                return tpllib[data.extracted['template']]
            except KeyError:
                pass
        return UNSET

    def template_vocabulary(self, widget, data):
        vocab = [
            ('-', _('no_template_selected', default=u'No template selected')),
        ]
        tpllib = IDynamicMailTemplateLibrary(self.context)
        for key in tpllib.keys():
            vocab.append((key, key))
        return vocab

    def text_value(self, widget, data):
        return UNSET

    def validate_tpl(self, widget, data):
        if not data.extracted:
            return data.extracted
        state, msg = TEMPLATE.validate(data.extracted.decode('utf8'))
        if not state:
            raise ExtractionError(msg)
        return data.extracted

    def send(self, widget, data):
        # uids get hooked up by JS in ``orders.notification_form_binder``
        uids = [_ for _ in self.request.form.get('uids', []) if _]
        print uids

    def ajax_url(self, widget, data):
        url = "{0}/@@load_notification_template".format(
            self.context.absolute_url()
        )
        return {'tplurl': url}

    def send_success(self, request):
        message = _('customers_notified_success',
                    default=u'Mail to customers sent')
        continuation = [
            AjaxOverlay(close=True),
            AjaxMessage(message, 'info', None)
        ]
        ajax_continue(self.request, continuation)
        return True

    def __call__(self):
        ajax_form_fiddle(
            self.request, 'form[id=form-notify_customers]', 'replace')
        return self.render_form()


class LoadTemplate(BrowserView):

    def __call__(self):
        self.request.response.setHeader('Content-Type', 'application/json')
        tpllib = IDynamicMailTemplateLibrary(self.context)
        tpl = tpllib[self.request.form['name']]
        return json.dumps({'tpl': tpl})
