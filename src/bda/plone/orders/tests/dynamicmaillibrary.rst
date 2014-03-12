Basic testing of DynamicMailTemplateLibrary
===========================================

Setup Test Env
--------------

Set up ZCA::

    >>> from bda.plone.orders.interfaces import IDynamicMailTemplateLibraryStorage
    >>> from bda.plone.orders.mailtemplates import DynamicMailTemplateLibraryAquierer
    >>> from bda.plone.orders.mailtemplates import DynamicMailTemplateLibraryStorage

    >>> from zope.annotation.interfaces import IAttributeAnnotatable
    >>> from zope.component import provideAdapter
    >>> from zope.interface import implementer

    >>> @implementer(IAttributeAnnotatable)
    ... class MockAcquiererContext(object): pass

    >>> provideAdapter(DynamicMailTemplateLibraryAquierer, (MockAcquiererContext,))

    >>> @implementer(IAttributeAnnotatable)
    ... class MockStorageContext(object): pass

    >>> provideAdapter(DynamicMailTemplateLibraryStorage,
    ...                (MockStorageContext,),
    ...                provides=IDynamicMailTemplateLibraryStorage)


provide some mock data tree::

    >>> mock_root = MockAcquiererContext()
    >>> mock_root.__parent__ = None

    >>> mock_lvl1 = MockAcquiererContext()
    >>> mock_lvl1.__parent__ = mock_root

    >>> mock_lvl2 = MockStorageContext()
    >>> mock_lvl2.__parent__ = mock_lvl1

    >>> mock_lvl3 = MockAcquiererContext()
    >>> mock_lvl3.__parent__ = mock_lvl2

    >>> mock_lvl4 = MockStorageContext()
    >>> mock_lvl4.__parent__ = mock_lvl3

    >>> mock_lvl5 = MockAcquiererContext()
    >>> mock_lvl5.__parent__ = mock_lvl4

Tests
-----

prepare objects::

    >>> from bda.plone.orders.interfaces import IDynamicMailTemplateLibrary
    >>> lib_root = IDynamicMailTemplateLibrary(mock_root)
    >>> lib_lvl1 = IDynamicMailTemplateLibrary(mock_lvl1)
    >>> lib_lvl2 = IDynamicMailTemplateLibrary(mock_lvl2)
    >>> lib_lvl3 = IDynamicMailTemplateLibrary(mock_lvl3)
    >>> lib_lvl4 = IDynamicMailTemplateLibrary(mock_lvl4)
    >>> lib_lvl5 = IDynamicMailTemplateLibrary(mock_lvl5)

setitem only on storages::

    >>> try:
    ...     lib_root['fooroot'] = u'foo root'
    ... except NotImplementedError, e:
    ...     print e.message
    acquierer do not set on parent (permissions)

    >>> lib_lvl2['foo2'] = u'foo 2'

    >>> try:
    ...     lib_lvl3['foo3'] = u'foo 3'
    ... except NotImplementedError, e:
    ...     print e.message
    acquierer do not set on parent (permissions)

    >>> lib_lvl4['foo4'] = u'foo 4'

getitem bubbles up::

    >>> lib_lvl2['foo2']
    u'foo 2'

    >>> lib_lvl3['foo2']
    u'foo 2'

    >>> lib_lvl4['foo2']
    u'foo 2'

    >>> lib_lvl5['foo2']
    u'foo 2'

    >>> lib_lvl2['foo2']
    u'foo 2'

    >>> lib_lvl4['foo2'] = u'foo 2.1'

    >>> lib_lvl5['foo2']
    u'foo 2.1'

    >>> lib_lvl4['foo2']
    u'foo 2.1'

    >>> lib_lvl3['foo2']
    u'foo 2'

keys::

    TODO