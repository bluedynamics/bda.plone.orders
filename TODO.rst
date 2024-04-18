TODO
====

- Fix bookings views filters.

- Store cart and item discount rules in checkout adapter instead of actual
  discount values in order to reliably modify orders while keeping invoice and
  order summary views sane.

- Rename salaried to paid all over the place.

- Icons in orders view actions.

- Icons in contacts view actions.

- Overhaul order view. Display discounted item price, etc.

- Think about adding notification text to booking data in checkout adapter if
  we want to display related text in invoice.

- Add vendor support to invoices.

- Properly implement initially non-billable bookings. Add a flag
  ``charge_if_backorder`` to ``IStockBehavior``, so we have control per buyable
  item, and a control panel setting with the default of this value
  for all buyables. Implement UI to carry back unbilled backorders. Adopt order
  and invoive views (Issue #45).

- Adopt text notification mail generation to mako templates and move existing
  text mail generation to legacy module, with flag to switch between old and
  new style text generation. As fallback add transformation of HTML mail to
  plain text version.
  (https://github.com/collective/Products.EasyNewsletter/blob/master/Products/EasyNewsletter/utils/mail.py#L112)

- @@orders in lineage subsites should only list orders in that path.

- Consider vendor UID's and booking based state in mail notification.

- Add ``is_customer`` utility.

- Improve customers vocabulary utility to be more cpu friendly.

- Search text in orders view needs to consider vendor and customer filter.

- Display Export orders link only for vendors and administrators.

- Work internally with unicode only.

- Move IUUID adapter for ``IPloneSiteRoot`` to ``bda.plone.cart``, which is the
  central package for the shop.

- ``cart_discount_net`` and ``cart_discount_vat`` values calculation for vendor
  specific orders in order view and order export.

- Warning-popup, if state is changed globally for all bookings in orders view.

- Move Customer role to ``bda.plone.cart``.

- Fix dependency in bda.plone.payment.cash.__init__, which depends on
  ``bda.plone.orders``.

- Move some interfaces to ``bda.plone.cart`` to avoid circular dependencies.
