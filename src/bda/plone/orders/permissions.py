from Products.CMFCore.permissions import setDefaultRoles

# view individual order
ViewOrderDirectly = 'bda.plone.orders: View Order Directly'
setDefaultRoles(ViewOrderDirectly,
                ('Manager', 'Site Administrator', 'Authenticated'))

# view own orders
ViewOwnOrders = 'bda.plone.orders: View Own Orders'
setDefaultRoles(ViewOwnOrders,
                ('Manager', 'Site Administrator', 'Authenticated'))

# view all orders
ViewOrders = 'bda.plone.orders: View Orders'
setDefaultRoles(ViewOrders,
                ('Manager', 'Site Administrator', 'Authenticated'))

# modify orders
ModifyOrders = 'bda.plone.orders: Modify Orders'
setDefaultRoles(ModifyOrders,
                ('Manager', 'Site Administrator', 'Vendor'))

# export orders
ExportOrders = 'bda.plone.orders: Export Orders'
setDefaultRoles(ExportOrders,
                ('Manager', 'Site Administrator', 'Vendor'))

# manage templates
ManageTemplates = 'bda.plone.orders: Manage Templates'
setDefaultRoles(ManageTemplates,
                ('Manager', 'Site Administrator', 'Vendor'))

# delegate customer role
DelegateCustomerRole = 'bda.plone.orders: Delegate Customer Role'
setDefaultRoles(DelegateCustomerRole,
                ('Manager', 'Site Administrator'))

# delegate vendor role
DelegateVendorRole = 'bda.plone.orders: Delegate Vendor Role'
setDefaultRoles(DelegateVendorRole,
                tuple())
