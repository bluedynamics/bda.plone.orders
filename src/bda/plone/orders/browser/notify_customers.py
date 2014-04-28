from Products.Five import BrowserView
from bda.plone.ajax import AjaxMessage
from bda.plone.ajax import AjaxOverlay
from bda.plone.ajax import ajax_continue
from bda.plone.ajax import ajax_form_fiddle
from bda.plone.orders import message_factory as _
from bda.plone.orders.browser.mailtemplates import TEMPLATE
from bda.plone.orders.common import OrderData
from bda.plone.orders.interfaces import IDynamicMailTemplateLibrary
from bda.plone.orders.mailnotify import MailNotify
from bda.plone.orders.vocabularies import salaried_vocab
from bda.plone.orders.vocabularies import state_vocab
from node.utils import UNSET
from yafowil.base import ExtractionError
from yafowil.plone.form import YAMLBaseForm
from zope.i18n import translate

import json


def mail_gender_vocab():
    return {
        '-': _('mister_misses', default=u'Mister/Misses'),
        'male': _('mister', default=u'Mister'),
        'female': _('misses', default=u'Misses'),
    }


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

    def _sendmail(self, notifier, uid, tpl, subject):
        order_data = OrderData(self.context, uid=uid)
        order = order_data.order
        data = {}
        for key in TEMPLATE.defaults:
            # XXX: refactor and use configurable callbacks
            # special case gender
            if key == 'personal_data.gender':
                data[key] = translate(mail_gender_vocab()[order.attrs[key]],
                                      context=self.request)
                continue
            # special case salaried
            if key == 'salaried':
                data[key] = translate(salaried_vocab()[order_data.salaried],
                                      context=self.request)
                continue
            # special case state
            if key == 'state':
                data[key] = translate(state_vocab()[order_data.state],
                                      context=self.request)
                continue
            # read attrs from order
            if key in order.attrs:
                data[key] = order.attrs[key]
        body = TEMPLATE(tpl, data).encode('utf-8')
        notifier.send(subject, body, order.attrs['personal_data.email'])

    def send(self, widget, data):
        tpl = data['text'].extracted.decode('utf8')
        subject = data['subject'].extracted.decode('utf8')
        notifier = MailNotify(self.context)
        for uid in self.request.form.get('uids', []):
            if not uid:
                continue
            self._sendmail(notifier, uid, tpl, subject)

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
        # XXX: security check -> current user has valid vandor area?
        ajax_form_fiddle(
            self.request, 'form[id=form-notify_customers]', 'replace')
        return self.render_form()


class LoadTemplate(BrowserView):

    def __call__(self):
        # XXX: security check -> current user has valid vandor area?
        self.request.response.setHeader('Content-Type', 'application/json')
        tpllib = IDynamicMailTemplateLibrary(self.context)
        try:
            tpl = tpllib[self.request.form['name']]
        except:
            tpl = ""
        return json.dumps({'tpl': tpl})
