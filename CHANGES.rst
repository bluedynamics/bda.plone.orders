Changelog
=========

2.0.dev0 (unreleased)
---------------------

- Update imports to reflect last cart/shipping chnages.
  [jensens]

- Bootstrapping rest endpoints and add first endpoint for order under ``@shop-order/ORDER_UID``.
  [jensens]

- Define features of OrderState, OrderData and BookingData in interfaces and let add implementer to classes.
  [jensens]

- Refactor out of `common.py` into different file to make development easier.
  [jensens]

- Remove Plone 4 specific ContentViewBase
  [jensens]

- Python 2/3 compatibility
  [agitator]

- Update version and classifiers - 2.x targets Plone 5.1/5.2 without Archetypes
  [agitator]


1.0a1 (unreleased)
------------------

- Remove ``Authenticated`` role for ``bda.plone.orders: View Orders``
  permission in ``rolmap.xml`` and add ``Vendor`` instead. We really do not
  want all authenticated users to be able to see all orders.
  [rnix]

- Move page templates to dedicated folder.
  [rnix]

- Move invoice related views from ``views.py`` to ``invoice.py``.
  [rnix]

- Move order related views from ``views.py`` to ``order.py``.
  [rnix]

- Move orders related views from ``views.py`` to ``orders.py``.
  [rnix]

- Move general views from ``views.py`` to ``common.py``.
  [rnix]

- Ajaxify cancel bookings.
  [rnix]

- Fix comment editing in plone 5.
  [rnix]

- Only display cancel booking action if booking not already cancelled.
  [rnix]

- Fix error in the order detail if the product no longer exists (#20).
  [rnix]

- Do not exclude reserved bookings by default from billing. This resolves
  inconsistenty introduced with
  https://github.com/bluedynamics/bda.plone.orders/pull/39 and addressed at
  https://github.com/bluedynamics/bda.plone.orders/issues/45.
  [rnix]

- Introduce ``ProtectedOrderDataView`` and use as base for ``DirectOrderView``
  and ``DirectInvoiceView``.
  [rnix]

- Add invoice view.
  [rnix]

- Remove duplicate ``Translate`` class from
  ``bda.plone.orders.browser.contacts``.
  [rnix]

- Rename ``OrdersContentView`` to ``ContentViewBase``.
  Introduce view configuration properties ``do_disable_border``,
  ``do_disable_left_column`` and ``do_disable_right_column``.
  [rnix]

- Introduce ``OrderDataView`` base class for views dealing with single order
  data.
  [rnix]

- Add HTML support for order related notification mails.
  [rnix]

- Change signature of ``bda.plone.orders.MailNotify.send``. Accepts now
  ``subject``, ``receiver`` and ``text`` as positional arguments and an
  optional ``html`` argument.
  [rnix]

- Also handle transaction id and payment state for ``bda.plone.stripe``
  payment in ``bda.plone.common.payment_success`` and
  ``bda.plone.common.payment_failed`` event subscribers.
  [rnix]

- @@orders: rebind notification binder also after datatable has been updated.
  [thet]

- Don't fail in ``@@contacts`` view when searching for non-ascii characters.
  [thet]

- Display Toolbar contents in Plone 5 on order related content views.
  [rnix]

- Fix export orders form.
  [rnix]

- Fix export if stock behavior not applied on buyable
  [rnix]

- use MwSt. instead of Ust. in german
  [agitator]

- Added item_number to order mails
  [agitator]

- Create safe filenames for ``@@exportorders_contextual``.
  [thet]

- Make the current context as base url for ``ajaxurl`` in OrdersTable and BookingsTable.
  This way, the current subsites settings are respected, e.g. when rendering state transition dropdowns, which again sends mails and those need the correct sender.
  [thet]

- Reimplement ``update_item_stock`` according to transition changes, documented at the table in ``transitions.py``.
  [thet]

- If no ``uid`` was given when calling the ``@@order`` view, redirect to current context and show an error message instead of failing.
  [thet]

- In ``@@bookings`` view, group by buyable per default.
  [thet]

- In ``@@bookings`` view, add ``buyable_comment`` column and combine first name, last name and address information to save space.
  [thet]

- Don't include reserved bookings in ``OrderData`` payment information (net, vat) and don't count them when calculating the salaried state for orders.
  [thet]

- In mail templates, list reserved items seperately from normal ordered items.
  [thet]

- Fix modifications of ``buyable_comment`` in ``@@orders`` view not being saved.
  [thet]

- Translate country code in mail notifications.
  [thet]

- On mail notifications, don't try to include delivery_address if no delivery_address template is available.
  In some contexts, there is no need for a delivery_address, like booking canceling.
  [thet]

- Unicode almost everywhere.
  Fixes some ``Unicode Decode Error``.
  [thet]

- Add transition actions when state is changed from "Reserved".
  Sends out a mail with a notification for the customer and adminitrator, that the item became available and is ordered.
  [thet]

- In ``do_transition_for`` on orders, set the state on each booking instead directly on the order.
  This way each booking setter is called, e.g. for changing stock items, setting overall order state and so on.
  [thet]

- Send out mails when cancelling whole orders or individual bookings from the ``@@orders`` and ``@@bookings`` views, not only from the order detail view.
  This is done by moving the necessary logic into ``bda.plone.orders.transitions.do_transition_for``.
  [thet]

- Add filters for Vendor, Customer, State and Salaried state to the @@bookings view.
  [pcdummy]

- Overhaul order and bookings state and salaried transitions.
  [rnix]

- Add filter for order state and salaried to the @@orders view.
  [pcdummy]

- Introduce ``bda.plone.orders.mailnotify.BOOKING_CANCELLED_TITLE_ATTRIBUTE``
  which is used to lookup title attribute for booking cancellation
  notification.
  [rnix]

- Fix sorting on email address in orders table.
  [rnix]

- Re-add calculated values for state and salaried on order booking. Needed
  for orders view to ensure sorting works.
  [rnix]

- Show user filter as "Lastname, Firstname (Username) - Email" instead of
  "Username (Firstname, Lastname)", sort the users on Lastname.
  [pcdummy]

- Plone 5 update
  [agitator]


0.9.dev
-------

- Set JSON response headers in ``TableData.__call__``.
  [rnix]

- Fix ``notify_customers`` view to work on any context. This allows for sending
  mail in the ``@@orders`` view when called somewhere else than ISite contexts.
  [thet]

- Fix indentation method in mailnotify module to handle non-ASCII data.
  [thet]

- Make orders view for whole site play nice with lineage.
  [jensens]

- Renew/Cancel Booking inc-/decreases stock now.
  Also some changes in API to be more consistent.
  [jensens]

- Cancel Booking now uses transition API.
  [jensens]

- JSON response header needed for @@contactsdata.
  [jensens]

- JSON response header needed for @@bookingsdata.
  [thet]

- JSHint JavaScript resources.
  [thet]

- fix: #24 error on submitting the checkout
  [jensens]

- feature: booking comment editable
  [jensens]

- feature: delete single booking from order
  [jensens]

- Move export related code in own file to reduce length and increase
  readability
  [jensens]

- Fix: Calculation of price in listings with a vat of zero failed.
  [jensens]

- Add two datatable views, in which bookings are displayed and can be grouped
  by the buyers email adress or the buyable uid. Both views support daterange
  filtering and text index support. The ``Bookings`` view gets called on the
  portal root and the ``Bookings in Context`` returns all bookings data on
  the corresponding context it is called.
  [benniboy]

- Major cleanup - code-analysis integrated, travis ci and moved IBuyable from
  bda.plone.shop to this package to avoid circular dependencies.
  [benniboy]

- Dont depend on implemented interfaces ITrading and IShippingItem.
  see https://github.com/bluedynamics/bda.plone.shop/issues/31
  [jensens]

- Fix item count validation in
  ``bda.plone.orders.common.OrderCheckoutAdapter.create_booking``.
  [rnix]

- added item price to item listing in order mail
  [agitator]

- added translated salutation to available mail template attributes
  [agitator]


0.8
---

- In ``@@order`` view, show state and salaried columns per booking, for the
  order notification email, indicate per booking, when it is reserved.
  [thet]


0.7
---

- Add ``buyable_available`` and ``buyable_overbook`` export attributes to CSV
  exports.
  [thet]

- Use ``csv.QUOTE_MINIMAL`` for CSV writers.
  [rnix]

- Decode strings to unicode in ``DynamicMailTemplate.normalized``.
  [rnix]

- Aquire until ``IPloneSiteRoot`` instead of ``ISite`` in
  ``acquire_vendor_or_shop_root``. ``lineage.subsite`` also works with
  ``ISite`` interface, but we really want to use plone root as fallback vendor
  if no object providing ``IVendor`` found in acquisition chain.
  [rnix]

- Instead of ``plone.app.uuid.utils.uuidToObject`` use
  ``bda.plone.cart.get_object_by_uid``, which does the same but can handle
  ``uuid.UUID`` and string objects.
  [thet]


0.6
---

- Introduce ``ViewOwnOrders`` (``bda.plone.orders: View Own Orders``) to
  protect ``@@myorders`` and descendant views with a dedicated permission.
  [thet]


0.5
---

- Add ``bda.plone.orders.ExportOrders`` permission and bind export related
  views to it.
  [rnix]

- Fix ``PaymentData.description`` unicode error.
  [rnix]

- Add upgrade step to reset all soup records attributes storage.
  [rnix]

- Include ``jquery-barcode`` from http://barcode-coder.com - not delivered to
  the client or used yet.
  [rnix]

- Include ``qrcode.js`` from http://davidshimjs.github.io/qrcodejs/ and render
  QR Code for order uuid in order view.
  [rnix]

- Move Javascript and CSS to resources folder.
  [rnix]

- Add ``bda.plone.orders.interfaces.ITrading`` and consider contract when
  creating order bookings.
  [rnix]

- Translate ``customers_notified_success`` ajax message directly in view class.
  [rnix]

- Add ``shippable`` flag to order bookings and implement upgrade step.
  [rnix]

- Remove ``bda.plone.orders.common.SKIP_PAYMENT_IF_RESERVED``. Equivalent
  exists now in ``bda.plone.shop`` controlpanel settings (**Attention** -
  default value changed to False there).
  [rnix]

- Always check for reservations in orders to select used mail templates no
  matter if mail gets send after checkout or after payment.
  [rnix]

- Rename ``bda.plone.orders.mailnotify.notify_reservation_if_payment_skipped``
  to ``bda.plone.orders.mailnotify.notify_checkout_success`` and use
  ``bda.plone.checkout.interfaces.ICheckoutSettings`` to check whether
  notification mail should be sent after checkout has been done.
  [rnix]

- Adopt ``bda.plone.checkout`` interfaces changes in
  ``bda.plone.orders.common.ICheckoutAdapter``.
  [rnix]

- Rename ``@@reservation_done`` view to ``@@order_done`` and handle displayed
  heading and text by order state.
  [rnix]

- Use ``OrderData.currency`` instead of ``ICartDataProvider.currency`` in
  ``bda.plone.orders.common.PaymentData.currency``.
  [rnix]

- Rename ``bda.plone.orders.mailnotify.create_order_total`` to
  ``bda.plone.orders.mailnotify.create_order_summary``.
  [rnix]

- Rename ``order_total`` to ``order_summary`` in order notification mail
  templates. **Note** - Update your template customizations
  [rnix]

- Add ``currency`` property to ``OrderData`` object.
  [rnix]

- Store ``payment_method`` and ``payment_label`` on order and provide upgrade
  step.
  [rnix]

- Implement summary listing for notification mails.
  [rnix]

- Change ``IPaymentText.payment_text`` from property to function and accept
  payment method id as argument.
  [rnix]

- Add ``@@exportorders_contextual`` view to export all orders of a context and
  below.
  [thet]

- Adopt shipping handling to ``bda.plone.shipping`` >= 0.4.
  [rnix]

- Introduce ``INotificationSettings`` which provides ``admin_name`` and
  ``admin_email`` attributes. Use these settings for sending notifications.
  [fRiSi, rnix]


0.4
---

- Change browser view and adapter regitrations from ``IPloneSiteRoot`` to
  ``zope.component.interfaces.ISite``. That's needed for Lineage compatibility.
  [thet]

- Integrate ``@@showorder`` view to access information for a specific order for
  anonymous users by giving the ordernumber and email as credentials.
  [thet]

- Fix mail sending for AT based buyable items.
  [rnix]

- Disable Diazo Theming for orders table
  [ezvirtual, rnix]

- Bind ``PaymentData`` adapter to interface instead of content class
  [ezvirtual]

- Integrate discounting information to orders and bookings.
  [rnix]

- Move state, salaried and tid to bookings.
  [thet]

- Order can have state ``processing``.
  [rnix]

- Add ``bda.plone.orders.permissions`` and call ``setDefaultRoles`` for
  contained permissions.
  [rnix]

- Also register ``bda.plone.orders.common.OrderCheckoutAdapter`` for
  ``Products.CMFPlone.interfaces.IPloneSiteRoot``.
  [rnix]

- Restrict orders and bookings in ``@@exportorders`` to what the user is
  allowed to see.
  [thet]

- Include Booking URL in ``@@exportorders``. Titles can easily be ambiguous.
  [thet]

- Introduce ``bda.plone.orders.interfaces.IItemNotificationText``,
  ``bda.plone.orders.interfaces.IGlobalNotificationText`` and
  ``bda.plone.orders.interfaces.IPaymentText`` used for mail notification
  after checkout.
  [rnix, jensens]

- ``OrderCheckoutAdapter`` no longer fails if uid in cart cookie which item
  not exists any longer.
  [rnix]

- Implement dedicated ``create_booking`` function in ``OrderCheckoutAdapter``
  for better customization purposes.
  [rnix]

- Implement multi client functionality with ``Vendor`` role and appropriate
  permissions. Assign bookings to vendors. Allow definitions of vendor areas
  via the ``IVendor`` interface.
  [thet, rnix]

- Introduce ``Customer`` Role.
  [thet, rnix]

- Render a link to the booked item in ``@@order`` view.
  [thet]

- Fix BrowserLayer order precedence.
  [thet]

- Copy all order data in ``create_mail_body`` to the template attributes to
  support custom (string)fields out of the box in mail templates.
  [fRiSi, rnix]

- ``bda.plone.orders.common.OrderData`` now accepts either ``uid`` or ``order``
  as keyword argument, and optional ``vendor_uid`` in ``__init__``.
  [rnix]


0.3
---

- ``bda.plone.payment.six_payment.ISixPaymentData`` has been removed. Use
  ``bda.plone.payment.interfaces.IPaymentData`` instead.
  [rnix]


0.2
---

- consider cart item stock where necessary.
  [rnix]

- Use Mailhost do send emails (see documentation_) to support
  setups with products such as `Products.PrintingMailHost`_
  [fRiSi]

  .. _documentation: http://plone.org/documentation/manual/upgrade-guide/version/upgrading-plone-3-x-to-4.0/updating-add-on-products-for-plone-4.0/mailhost.securesend-is-now-deprecated-use-send-instead
  .. _`Products.PrintingMailHost`: https://pypi.python.org/pypi/Products.PrintingMailHost/0.7


0.1
---

- initial work
  [rnix]
