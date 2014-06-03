================
bda.plone.orders
================


Installation
============

This package is part of the `bda.plone.shop`_ stack. Please refer to
https://github.com/bluedynamics/bda.plone.shop for installation
instructions.


Integration notes
=================

- The order actions are done with background images in CSS, so if you have your
  own theme that is not based on Sunburst, you will have to add the "icons.on"
  part of Sunburst's base.css.


Customizing Orders
==================

If you've added custom fields to the checkout (see
`bda.plone.checkout`_), chances are high you want to add them to the
order emails, order summaries or the order export.

.. _`bda.plone.checkout`: https://github.com/bluedynamics/bda.plone.checkout

Please follow the instructions in `Customizing the shop` in the
`bda.plone.shop`_ Readme first to setup the patch infrastructure.

.. _`bda.plone.shop`: https://github.com/bluedynamics/bda.plone.shop

 After that you can start customizing the order process::
 
    def patchShop():
        patchMailTemplates()
        patchOrderExport()


Mail notifications
------------------

Copy the messages you need to customize from
``bda.plone.orders.mailtemplates`` and change the
text to your needs.::

    ORDER_BODY_EN = """
    This is my heavily customized confirmation mail."""

    RESERVATION_BODY_EN = """
    This is the heavily customized text sent to users
    having one or more items in the order that ran out of stock and have
    been reserved"""

    from bda.plone.orders import mailtemplates as original_templates

    def patchMailTemplates():
        original_templates.ORDER_BODY_EN = ORDER_BODY_EN
        original_templates.ORDER_TEMPLATES['en']['body'] = ORDER_BODY_EN

        original_templates.RESERVATION_BODY_EN = RESERVATION_BODY_EN
        original_templates.RESERVATION_TEMPLATES['en']['body'] = \
            RESERVATION_BODY_EN

When updating ``bda.plone.shop`` to a new version, make sure to keep them
in sync with the original templates and check if all stock variables
(such as ``global_text`` or the ``@@showorder`` link which have been
added in version 0.4 are present.)


Order Export
------------

To make a new field show up in the export, just add it to the
list ``ORDER_EXPORT_ATTRS``.

In this example we include the company uid we added in the example for
customizing ``bda.plone.checkout`` right after the company name::

    from bda.plone.orders.browser.views import ORDER_EXPORT_ATTRS

    def patchOrderExport():
        idx = ORDER_EXPORT_ATTRS.index('personal_data.company')
        ORDER_EXPORT_ATTRS.insert(idx+1, 'personal_data.uid')


Order details
-------------

To show the data of the new field in the detail view of the order
customize ``bda/plone/orders/browser/order.pt`` using
`z3c.jbot <https://pypi.python.org/pypi/z3c.jbot>`_ or by registering
the page for your policy package's browserlayer or themelayer::

    <browser:page
      for="zope.component.interfaces.ISite"
      name="order"
      template="my-order.pt"
      class="bda.plone.orders.browser.views.OrderView"
      permission="bda.plone.orders.ViewOrders"
      layer="my.package.interfaces.IMyBrowserLayer"/>


Restrictions with souper.plone
==============================

- Make sure you do not move orders or bookings soup away from portal root. This
  will end up in unexpected behavior and errors.


Permissions
===========

In general, custom shop deployments are likely to configure the permission and
role settings according to their use cases.

The Permissions ``bda.plone.orders.ViewOrderDirectly`` and
``bda.plone.orders.ViewOrders`` are granted to default Plone roles rather
than Customer role, because the Customer role can be granted as a local role
contextually, where the ``@@orders`` and ``@@showorder`` views should be
callable on ``ISite`` root. So a possible customer might be no customer on the
site root.


Permission ``bda.plone.orders.ViewOrderDirectly``
-------------------------------------------------

TODO: document


Permission ``bda.plone.orders.ViewOwnOrders``
---------------------------------------------

TODO: document


Permission ``bda.plone.orders.ViewOrders``
------------------------------------------

TODO: document


Permission ``bda.plone.orders.ModifyOrders``
--------------------------------------------

TODO: document


Permission ``bda.plone.orders.ExportOrders``
--------------------------------------------

TODO: document


Permission ``bda.plone.orders.ManageTemplates``
-----------------------------------------------

TODO: document


Permission ``bda.plone.orders.DelegateCustomerRole``
----------------------------------------------------

TODO: document


Permission ``bda.plone.orders.DelegateVendorRole``
--------------------------------------------------

TODO: document



Create translations
===================

::

    $ cd src/bda/plone/orders/
    $ ./i18n.sh


TODO
====

- @@orders in lineage subsites should only list orders in that path.

- Consider vendor UID's and booking based state in mail notification

- add is_customer utility

- improve customers vocabulary utility to be more cpu friendly

- search text in orders view needs to consider vendor and customer filter

- Display Export orders link only for vendors and administrators

- Work internally with unicode only.


TODO Future
===========

- Move IUUID adapter for IPloneSiteRoot to bda.plone.cart, which is the central
  package for the shop.

- cart_discount_net and cart_discount_vat values calculation for vendor specific
  orders in order view and order export.

- skip payment for individual bookings instead of whole order, if they are in
  state reserved.

- warning-popup, if state is changed globally for all bookings in @@orders view

- buyable_uid, buyable_count, buyable_comment -> should be named cartitem_*?

- customer role -> move to bda.plone.cart

- eventually create common.BookingTransitions and common.BookingData

- fix dependency in bda.plone.payment.cash.__init__, which depends on b.p.orders

- eventually create: or bda.shop, which defines the interfaces. every other
  package can depend on, which eases the dependency chain


Contributors
============

- Robert Niederreiter (Author)
- Johannes Raggam
- Peter Holzer
- Harald Frießnegger
- Ezra Holder

