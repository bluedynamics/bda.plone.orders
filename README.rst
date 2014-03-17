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


Contributors
------------

- Robert Niederreiter (Author)
- Harald Frießnegger
- Peter Holzer
- Johannes Raggam
