from interlude import interact
from plone.testing import layered
from plone.testing.zca import UNIT_TESTING

import doctest
import os
import pprint
import unittest


optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

TESTFILES = [
    ('mailtemplates.rst', UNIT_TESTING),
]

def test_suite():
    return unittest.TestSuite([
        layered(
            doctest.DocFileSuite(
                filename,
                optionflags=optionflags,
                globs={
                    'interact': interact,
                    'pprint': pprint.pprint,
                },
            ), layer=layer
        )
        for filename, layer in TESTFILES]
    )
