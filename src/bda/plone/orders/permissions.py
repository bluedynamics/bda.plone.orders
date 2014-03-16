from Products.CMFCore.permissions import setDefaultRoles


ViewOrders = 'bda.plone.orders: View Orders'
setDefaultRoles(ViewOrders,
                ('Manager', 'Site Administrator', 'Vendor', 'Customer'))

AllOrders = 'bda.plone.orders: All Orders'
setDefaultRoles(AllOrders,
                ('Manager', 'Site Administrator'))

VendorOrders = 'bda.plone.orders: Vendor Orders'
setDefaultRoles(VendorOrders,
                ('Manager', 'Site Administrator', 'Vendor'))

CustomerOrders = 'bda.plone.orders: Customer Orders'
setDefaultRoles(CustomerOrders,
                ('Manager', 'Site Administrator', 'Vendor', 'Customer'))

ModifyOrders = 'bda.plone.orders: Modify Orders'
setDefaultRoles(ModifyOrders,
                ('Manager', 'Site Administrator', 'Vendor'))

DelegateVendorRole = 'bda.plone.orders: Delegate Vendor Role'
setDefaultRoles(DelegateVendorRole, tuple())
