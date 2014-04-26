
Changelog
=========

0.5dev
------

- Introduce ``INotificationSettings`` which provides ``admin_name`` and
  ``admin_email`` attributes. Use these settings for sending notifications.
  [fRiSi, rnix]


0.4
---

- Change browser view and adapter regitrations from IPloneSiteRoot to
  `zope.component.interfaces.ISite`. That's needed for Lineage compatibility.
  [thet]

- Integrate @@showorder view to access information for a specific order for
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
