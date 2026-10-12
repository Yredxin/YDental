{
    'name': 'YDental Inventory',
    'author': 'YDental',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['stock', 'product', 'uom', 'product_expiry', 'ydental_access', 'ydental_intake', 'ydental_queue'],
    'data': ['security/ir.access.csv', 'data/ydental_inventory_data.xml', 'views/ydental_inventory_templates.xml'],
    'installable': True,
}
