
Changelog
=========

0.5dev
------

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
  ``bda.plone.orders.mailnotify.create_order_summery``.
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
