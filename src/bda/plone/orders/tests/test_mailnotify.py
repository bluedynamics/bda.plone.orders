# -*- coding: utf-8 -*-
from bda.plone.orders import mailnotify as MN

import unittest


class TestMailnotifyUnit(unittest.TestCase):
    def test_indent_wrap(self):
        """The _indent mehtod should wrap like defined by it's parameters.
        """
        txt = u"abcd " * 3
        ctrl = '     abcd\nabcd abcd'  # textwrap removes whitespace at EOL
        res = MN._indent(txt, width=10, ind=5)
        self.assertEqual(res, ctrl)

    def test_indent_unicode(self):
        """The _indent method should be able to handle non-ASCII data.
        """
        txt = 'äüöß ' * 3
        ctrl = u'äüöß äüöß\näüöß'  # textwrap removes whitespace at EOL
        res = MN._indent(txt, width=10, ind=0)
        self.assertEqual(res, ctrl)
