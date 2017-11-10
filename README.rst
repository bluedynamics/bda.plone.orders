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

After that you can start customizing the order process:

.. code-block:: python

    def patchShop():
        patchMailTemplates()
        patchOrderExport()


Mail notifications
------------------

Order related notification is done by sending multipart mails containing a
text and a HTML version of the notification payload.

When customizing mail notification, both text and HTML templates needs to be
customized.

.. warning::

    As of ``bda.plone.orders`` 1.0a1, signatue of
    ``bda.plone.orders.MailNotify.send`` changed. It accepts now
    ``subject``, ``receiver`` and ``text`` as positional arguments and an
    optional ``html`` argument.


HTML Templates
~~~~~~~~~~~~~~

Default HTML templates are located at ``bda.plone.orders:mailtemplates``.
To customize them, copy the entire template folder to your integration package
and patch ``bda.plone.orders.mailnotify.MAIL_TEMPLATES_DIRECTORY`` like so:

.. code-block:: python

    from bda.plone.orders import mailnotify
    import os

    mailnotify.MAIL_TEMPLATES_DIRECTORY = os.path.join(
        os.path.dirname(__file__),
        'mailtemplates'
    )


Text Templates
~~~~~~~~~~~~~~

Copy the messages you need to customize from
``bda.plone.orders.mailtemplates`` and change the text to your needs.
There are two dictionaries containing all the strings, ``ORDER_TEMPLATES``
and ``RESERVATION_TEMPLATES``. Its a nested dict. On the first level is the
langugae code, the second level is ``subject``, ``body`` and
``delivery_address``. Change them i.e. like this:

.. code-block:: python

    from bda.plone.orders.mailtemplates import ORDER_TEMPLATES
    from bda.plone.orders.mailtemplates import RESERVATION_TEMPLATES

    ORDER_TEMPLATES['en']['body'] = """
    This is my heavily customized confirmation mail."""

    RESERVATION_TEMPLATES['de']['body'] = "Ihre Reservierung ist da!"

When updating ``bda.plone.order`` to a new version, make sure to keep them
in sync with the original templates and check if all stock variables
(such as ``global_text`` or the ``@@showorder`` link which have been
added in version 0.4 are present.)


Customize notification mechanism
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alternativly you add/replace the notification methods and implement your
own very custom. To do provide your own two functions similar to
``bda.plone.orders.mailnotify.notify_checkout_success`` and
``bda.plone.orders.mailnotify.notify_payment_success``. Then

.. code-block:: python

    from bda.plone.orders.mailnotify import NOTIFICATIONS

    # register as additional action
    NOTIFICATIONS['checkout_success'].append(my_notify_checkout_success)
    NOTIFICATIONS['payment_success'].append(my_notify_payment_success)

    # OR
    # register as replacement:
    NOTIFICATIONS['checkout_success'] = [my_notify_checkout_success]
    NOTIFICATIONS['payment_success'] = [my_notify_payment_success]


Order Export
------------

To make a new field show up in the export, just add it to the
list ``ORDER_EXPORT_ATTRS``.

In this example we include the company uid we added in the example for
customizing ``bda.plone.checkout`` right after the company name:

.. code-block:: python

    from bda.plone.orders.browser.views import ORDER_EXPORT_ATTRS

    def patchOrderExport():
        idx = ORDER_EXPORT_ATTRS.index('personal_data.company')
        ORDER_EXPORT_ATTRS.insert(idx+1, 'personal_data.uid')


Order details
-------------

To show the data of the new field in the detail view of the order
customize ``bda/plone/orders/browser/order.pt`` using
`z3c.jbot <https://pypi.python.org/pypi/z3c.jbot>`_ or by registering
the page for your policy package's browserlayer or themelayer:

.. code-block:: xml

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


How To allow anonymous users to buy items
=========================================

In your Generic Setup's profile, add to ``rolemap.xml``:

.. code-block:: xml

    <!-- Allow Anonymous to buy items -->
    <permission name="bda.plone.orders: View Order Directly" acquire="True">
      <role name="Manager" />
      <role name="Site Administrator" />
      <role name="Authenticated" />
      <role name="Anonymous"/>
    </permission>
    <permission name="bda.plone.shop: View Buyable Info" acquire="True">
      <role name="Manager" />
      <role name="Site Administrator" />
      <role name="Reviewer" />
      <role name="Editor" />
      <role name="Customer" />
      <role name="Anonymous"/>
    </permission>
    <permission name="bda.plone.shop: Modify Cart" acquire="True">
      <role name="Manager" />
      <role name="Site Administrator" />
      <role name="Customer" />
      <role name="Anonymous"/>
    </permission>
    <permission name="bda.plone.checkout: Perform Checkout" acquire="True">
      <role name="Manager" />
      <role name="Site Administrator" />
      <role name="Customer" />
      <role name="Anonymous"/>
    </permission>


Create translations
===================

::

    $ cd src/bda/plone/orders/
    $ ./i18n.sh


TODO
====

- Add vendor support to invoices.

- Add a flag ``charge_if_backorder`` to ``IStockBehavior``, so we have control
  per buyable item, and a control panel setting with the default of this value
  for all buyables (Issue #45).

- Adopt text notification mail generation to mako templates and move existing
  text mail generation to legacy module, with flag to switch between old and
  new style text generation. As fallback add transformation of HTML mail to
  plain text version.
  (https://github.com/collective/Products.EasyNewsletter/blob/master/Products/EasyNewsletter/utils/mail.py#L112)

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
- Benjamin Stefaner (benniboy)

Icons used are `Silk-Icons by FamFamFam <http://www.famfamfam.com/lab/icons/silk/>`_ under CC-BY 2.5 license.
