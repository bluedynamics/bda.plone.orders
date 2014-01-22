
Changelog
=========

0.4dev
------

- Introduce ``IVendor`` interface.
  [rnix]

- Copy all order data in ``create_mail_body`` to the template attributes to
  support custom (string)fields out of the box in mail templates.
  [fRiSi, rnix]

- ``bda.plone.orders.common.OrderData`` now accepts either ``uid`` or ``order``
  as keyword argument in ``__init__``.
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
