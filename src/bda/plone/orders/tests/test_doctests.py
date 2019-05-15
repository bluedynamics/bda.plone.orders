# -*- coding: utf-8 -*-
from bda.plone.orders.tests import Orders_INTEGRATION_TESTING
from interlude import interact
from plone.testing import layered
from plone.testing.zca import UNIT_TESTING

import doctest
import pprint  # noqa
import unittest


optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

TESTFILES = [
    ('dynamicmailtemplate.rst', UNIT_TESTING),
    ('dynamicmaillibrary.rst', Orders_INTEGRATION_TESTING),
]


def test_suite():
    return unittest.TestSuite(
        [
            layered(
                doctest.DocFileSuite(
                    filename,
                    optionflags=optionflags,
                    globs={'interact': interact, 'pprint': pprint.pprint},  # noqa
                ),
                layer=layer,
            )
            for filename, layer in TESTFILES
        ]
    )
