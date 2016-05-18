# -*- coding: utf-8 -*-
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
import urllib


class BaseDropdown(object):
    render = ViewPageTemplateFile('dropdown.pt')
    name = ''
    css = 'dropdown'
    action = ''
    subtype = ''
    vocab = {}
    transitions = {}
    value = ''

    def __init__(self, context, request, record):
        self.context = context
        self.request = request
        self.record = record

    def create_items(self, transitions):
        """create and return available transitions for dropdown
        """
        ret = list()
        url = self.context.absolute_url()
        params = {
            'uid': str(self.record.attrs['uid']),
            'subtype': self.subtype,
        }
        vendor = self.request.form.get('vendor', '')
        if vendor:
            params['vendor'] = vendor
        for transition in transitions:
            params['transition'] = transition
            target = '?'.join([url, urllib.urlencode(params)])
            ret.append({
                'title': self.transitions[transition],
                'target': target,
            })
        return ret

    @property
    def identifyer(self):
        return '%s-%s' % (self.name, str(self.record.attrs['uid']))

    @property
    def ajax_action(self):
        return '%s:#%s-%s:replace' % (self.action,
                                      self.name,
                                      str(self.record.attrs['uid']))

    @property
    def items(self):
        raise NotImplementedError(u"Abstract Dropdown does not implement "
                                  u"``items``.")
