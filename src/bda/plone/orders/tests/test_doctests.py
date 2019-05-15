# -*- coding: utf-8 -*-
from bda.plone.orders.tests import Orders_INTEGRATION_TESTING
from plone.testing import layered
from plone.testing.zca import UNIT_TESTING

import doctest
import pprint  # noqa
import unittest


optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

TESTFILES = [
    ("dynamicmailtemplate.rst", UNIT_TESTING),
    ("dynamicmaillibrary.rst", Orders_INTEGRATION_TESTING),
]


def test_suite():
    return unittest.TestSuite(
        [
            layered(
                doctest.DocFileSuite(
                    filename, optionflags=optionflags, globs={"pprint": pprint.pprint}
                ),
                layer=layer,
            )
            for filename, layer in TESTFILES
        ]
    )
