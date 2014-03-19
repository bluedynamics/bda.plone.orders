================
bda.plone.orders
================


Installation
------------

This package is part of the ``bda.plone.shop`` stack. Please refer to
``https://github.com/bluedynamics/bda.plone.shop`` for installation
instructions.


Integration notes
-----------------

- The order actions are done with background images in CSS, so if you have your
  own theme that is not based on Sunburst, you will have to add the "icons.on"
  part of Sunburst's base.css.


Restrictions with souper.plone
------------------------------

- Make sure you do not move orders or bookings soup away from portal root. This
  will end up in unexpected behavior and errors.


Create translations
-------------------

::

    $ cd src/bda/plone/orders/
    $ ./i18n.sh


TODO
----

OK - Store order state on each booking to make it possible each vendor can handle
  state of bookings in order belonging to him

OK - Adopt order transitions affecting only bookings belonging to vendor
  triggering the change

OK - Extend plone.app.workflow to throw a LocalrolesModifiedEvent

- Add customer_role index storing all usernames which have customer role on
  several areas of the portal

- as is_customer utility

- improve customers vocabulary utility to be more cpu friendly

- search text in orders view needs to consider vendor and customer filter

- ajaxify orders table if filters get changed

- skip payment for individual bookings instead of whole order, if they are in
  state reserved.

- warning-popup, if state is changed globally for all bookings in @@orders view

- buyable_uid, buyable_count, buyable_comment -> should be named cartitem_*?

- customer role -> gehörert in bda.plone.cart rein

- eventually create common.BookingTransitions and common.BookingData

- fix dependency in bda.plone.payment.cash.__init__, which depends on b.p.orders

- eventually create: or bda.shop, which defines the interfaces. every other
  package can depend on, which eases the dependency chain


Contributors
------------

- Robert Niederreiter (Author)
- Harald Frießnegger
- Peter Holzer
- Johannes Raggam
