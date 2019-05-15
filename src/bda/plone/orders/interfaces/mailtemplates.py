# -*- coding: utf-8 -*-
from zope.interface import Interface


class IDynamicMailTemplateLibrary(Interface):
    """A set of named templates.
    """

    def keys():
        """list names of templates.
        """

    def __getitem__(name):
        """return template by name.
        """


class IDynamicMailTemplateLibraryStorage(IDynamicMailTemplateLibrary):
    def direct_keys():
        """non acquired keys.
        """

    def __setitem__(name, template):
        """store template under a name.
        """

    def __delitem__(name):
        """remove template with this name.
        """
