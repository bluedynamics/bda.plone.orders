from plone import api


def reindex_customer_role(context, event):
    """Reindex ``customer_role`` index after local roles changed.
    """
    print("REINDEXING customer_role")
    catalog = api.portal.get_tool(name='portal_catalog')
    catalog.reindexObject(context,
                          idxs=['customer_role'],
                          update_metadata=0,
                          uid='/'.join(context.getPhysicalPath()))
