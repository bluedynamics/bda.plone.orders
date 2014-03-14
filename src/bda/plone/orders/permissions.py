from Products.CMFCore.permissions import setDefaultRoles


ViewOrders = 'bda.plone.orders: View Orders'
setDefaultRoles(ViewOrders, ('Manager', 'Shop Admin', 'Vendor', 'Customer'))

AllOrders = 'bda.plone.orders: All Orders'
setDefaultRoles(AllOrders, ('Manager', 'Shop Admin'))

VendorOrders = 'bda.plone.orders: Vendor Orders'
setDefaultRoles(VendorOrders, ('Manager', 'Shop Admin', 'Vendor'))

CustomerOrders = 'bda.plone.orders: Customer Orders'
setDefaultRoles(CustomerOrders, ('Manager', 'Shop Admin', 'Vendor', 'Customer'))

DelegateVendorRole = 'bda.plone.orders: Delegate Vendor Role'
setDefaultRoles(DelegateVendorRole, tuple())
