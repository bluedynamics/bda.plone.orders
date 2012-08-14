bda.plone.orders
================


Create translations
-------------------

::

    cd src/bda/plone/orders/
    
    i18ndude rebuild-pot --pot locales/bda.plone.orders.pot \
        --merge locales/manual.pot --create bda.plone.orders .
    
    i18ndude sync --pot locales/bda.plone.orders.pot \
        locales/de/LC_MESSAGES/bda.plone.orders.po
