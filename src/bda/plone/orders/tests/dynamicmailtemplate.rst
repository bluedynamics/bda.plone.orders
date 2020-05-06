Dynamic Mailtemplates
=====================

prepare
-------

::

    >>> from bda.plone.orders.mailtemplates import DynamicMailTemplate

    >>> defaults = {
    ...     u'uid': u'7372518394',
    ...     u'title': u'Millenium Falcon',
    ...     u'description': u'n/a',
    ... }

    >>> required = [u'uid', u'title']


validation at init time
-----------------------

required keys mus be available in defaults as well::

    >>> wrong_defaults = defaults.copy()
    >>> del wrong_defaults[u'title']
    >>> dmt = DynamicMailTemplate(required, wrong_defaults)
    Traceback (most recent call last):
    ...
    ValueError: All required must be in defaults too, missing: title

    >>> dmt = DynamicMailTemplate(required, defaults)


validation of template
----------------------

template must be unicode::

    >>> dmt = DynamicMailTemplate(required, defaults)

    >>> wrong_tpl = b'foo'
    >>> dmt.validate(wrong_tpl)
    Traceback (most recent call last):
    ...
    AssertionError: template must be unicode

    >>> dmt(wrong_tpl, defaults)
    Traceback (most recent call last):
    ...
    AssertionError: template must be unicode

accepted as unicode::

    >>> tpl = u'[{uid}] {title}: {description}'
    >>> dmt.validate(tpl)
    (True, '')

    >>> dmt(tpl, defaults)
    u'[7372518394] Millenium Falcon: n/a'

non-renderable::

    >>> tpl = u'[{uid}] {title}: {description} {nonexistent}'
    >>> dmt.validate(tpl)
    (False, u'Variable "nonexistent" is not available.')

    >>> tpl = u'[{uid}] {title}: {description:8.2f}'
    >>> dmt.validate(tpl)
    (False, "Unknown format code 'f' for object of type 'unicode'")


validation at rendering time
----------------------------

required keys must be in data::

    >>> tpl = u'[{uid}] {title}: {description}'
    >>> wrong_data = defaults.copy()
    >>> del wrong_data['uid']
    >>> dmt(tpl, wrong_data)
    Traceback (most recent call last):
    ...
    KeyError: 'Required key uid is missing.'

finally a working set::

    >>> tpl = u'[{uid}] {title}: {description}'
    >>> data = {
    ...     u'uid': u'192411350954',
    ...     u'title': u'Tie Fighter',
    ...     u'description': u'The därk side!',
    ... }
    >>> dmt(tpl, data)
    u'[192411350954] Tie Fighter: The d\xc3\xa4rk side!'



