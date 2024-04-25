bda.plone.orders
================

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

.. image:: https://travis-ci.org/bluedynamics/bda.plone.orders.svg?branch=master
    :target: https://travis-ci.org/bluedynamics/bda.plone.orders

Shop order storage and management.

This package is part of the ``bda.plone.shop`` stack. Please refer to
`bda.plone.shop <https://github.com/bluedynamics/bda.plone.shop>`_ for
installation instructions.


Integration notes
-----------------

- The order actions are done with background images in CSS, so if you have your
  own theme that is not based on Sunburst, you will have to add the "icons.on"
  part of Sunburst's base.css.


Customizing Orders
------------------

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
        patchOrderExport()


Mail notifications
~~~~~~~~~~~~~~~~~~

Order related notification is done by sending multipart mails containing a
text and a HTML version of the notification payload.

When customizing mail notification, both text and HTML templates needs to be
customized.

WARNING:

    As of ``bda.plone.orders`` 1.0a1, signatue of
    ``bda.plone.orders.MailNotify.send`` changed. It accepts now
    ``subject``, ``receiver`` and ``text`` as positional arguments and an
    optional ``html`` argument.


HTML Templates
^^^^^^^^^^^^^^

Default HTML templates are located at ``bda.plone.orders.mailnotifytemplates``
and registered as ``BrowserViews``. You can override the templates using
``z3c.jbot``.

WARNING:

    As of ``bda.plone.orders`` 2.0b3 the location of the mailnotification
    templates moved from the folder ``mailtemplates`` to the module
    ``mailnotifytemplates``. Please refactor your patches to jbot templates
    or BrowserViews.


Text Templates
^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
~~~~~~~~~~~~

To make a new field show up in the export, just add it to the
list ``ORDER_EXPORT_ATTRS``.

In this example we include the company uid we added in the example for
customizing ``bda.plone.checkout`` right after the company name:

.. code-block:: python

    from bda.plone.orders.browser.export import ORDER_EXPORT_ATTRS

    def patchOrderExport():
        idx = ORDER_EXPORT_ATTRS.index('personal_data.company')
        ORDER_EXPORT_ATTRS.insert(idx+1, 'personal_data.uid')


Order details
~~~~~~~~~~~~~

To show the data of the new field in the detail view of the order
customize ``bda/plone/orders/browser/templates/order.pt`` using
`z3c.jbot <https://pypi.python.org/pypi/z3c.jbot>`_ or by registering
the browser page for your policy package's browserlayer or themelayer:

.. code-block:: xml

    <browser:page
      for="zope.component.interfaces.ISite"
      name="order"
      template="my-order.pt"
      class="bda.plone.orders.browser.order.OrderView"
      permission="bda.plone.orders.ViewOrders"
      layer="my.package.interfaces.IMyBrowserLayer"/>

WARNING:

    as of ``bda.plone.orders`` 1.0a1 the template location changed from
    browser package to templates folder in browser package. Please adopt
    the location if you customized the template via ``z3c.jbot`` in your
    integration package.


Invoice view
~~~~~~~~~~~~

The invoice template is ``bda/plone/orders/browser/templates/invoice.pt``.
It can be customized via `z3c.jbot <https://pypi.python.org/pypi/z3c.jbot>`_ or
by registering the browser page for your policy package's browserlayer or
themelayer:

.. code-block:: xml

      <browser:page
        for="zope.component.interfaces.ISite"
        name="invoice"
        template="my-invoice.pt"
        class="bda.plone.orders.browser.invoice.InvoiceView"
        permission="bda.plone.orders.ViewOrders"
        layer="my.package.interfaces.IMyBrowserLayer" />


Restrictions with souper.plone
------------------------------

- Make sure you do not move orders or bookings soup away from portal root. This
  will end up in unexpected behavior and errors.


Vendor support
--------------

``bda.plone.orders`` supports the concept of vendors. A vendor is able to
manage his products and view orders and booking related to this products.

A vendor has his own area, which is a container somewhere in the portal.
To enable vendor support for a container, navigate to it and apply
``Enable vendor area`` action on it. Then navigate to local roles management
view of this container and grant ``Vendor`` role to the desired users.

The users granted the ``Vendor`` role is now able to see order related views
and perform order related actions in the context of this container.


Permissions
-----------

In general, custom shop deployments are likely to configure the permission and role settings according to their use cases.

The Permissions ``bda.plone.orders.ViewOrderDirectly`` and ``bda.plone.orders.ViewOwnOrders`` are granted to default Plone roles rather than Customer role.
The Customer role is intended to be granted as a local role contextually.
The ``@@orders`` and ``@@showorder`` and ``@@showinvoice`` views should be callable on ``ISite`` root.
So a possible customer might be no customer on the site root.

Following as listing of the permissions and its purpose:


``bda.plone.orders.ViewOrderDirectly``
    Grants view access to single order data related views,
    which are protected by ordernumber and related email address.

    Currently order details and invoice are implemented as such views.
    A link to them is sent in the order confirmation mail after successful checkout.

    By default, this permission is set for roles:

    * Manager
    * Site Administrator
    * Authenticated

    In order to expose this views to all visitors by default, add ``Anonymous``
    role via generic setup's ``rolemap.xml`` of your integration package.


``bda.plone.orders.ViewOwnOrders``
    Grants permission to view orders made by the currently authenticated user.

    By default, this permission is set for roles:

    * Manager
    * Site Administrator
    * Authenticated

    To customize this, edit ``rolemap.xml`` in your integration package as needed.


``bda.plone.orders.ViewOrders``
    Grants permission to view all orders in a given context or globally.

    By default, this permission is set for roles:

    * Manager
    * Site Administrator
    * Vendor

    To customize this, edit ``rolemap.xml`` in your integration package as needed.


``bda.plone.orders.ModifyOrders``
    Grants the user to modify orders.
    This includes to perform state transitions on orders and bookings, and to modify booking comments.

    By default, this permission is set for roles:

    * Manager
    * Site Administrator
    * Vendor

    To customize this, edit ``rolemap.xml`` in your integration package as needed.


``bda.plone.orders.ExportOrders``
    Grants the user to export orders in CSV format.

    By default, this permission is set for roles:

    * Manager
    * Site Administrator
    * Vendor

    To customize this, edit ``rolemap.xml`` in your integration package as needed.


``bda.plone.orders.ManageTemplates``
    Grants the user to manage notification mail templates for existing orders.

    By default, this permission is set for roles:

    * Manager
    * Site Administrator
    * Vendor

    To customize this, edit ``rolemap.xml`` in your integration package as needed.


``bda.plone.orders.DelegateCustomerRole``
    Grant the ``Customer`` role to other users via the localroles view.

    By default, this permission is set for roles:

    * Manager
    * Site Administrator

    To customize this, edit ``rolemap.xml`` in your integration package as needed.


``bda.plone.orders.DelegateVendorRole``
    Grants the user to grant the ``Vendor`` role to other users via the localroles view.

    By default, this permission is set for no roles.

    To customize this, edit ``rolemap.xml`` in your integration package as needed.


How To allow anonymous users to buy items
-----------------------------------------

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


REST-API
--------

There is a REST API available.
It is based on `plone.rest <https://pypi.org/project/plone.rest/>`_ endpoints.

The REST API is work in progress and will be enhanced over time.

We provide the following endpoints:

GET ``@shop-order/${ORDER-UID}``
    The order data of the order with the given order-uid.
    It includes bookings and the booking-data.


Create translations
-------------------

::

    $ cd src/bda/plone/orders/
    $ ./i18n.sh


Contributors
------------

- Robert Niederreiter (Author)
- Johannes Raggam
- Peter Holzer
- Harald Frießnegger
- Ezra Holder
- Benjamin Stefaner (benniboy)
- Jens Klein


Icons used are `Silk-Icons by FamFamFam <http://www.famfamfam.com/lab/icons/silk/>`_
under CC-BY 2.5 license.
