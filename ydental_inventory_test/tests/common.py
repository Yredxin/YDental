from datetime import timedelta
import secrets

from odoo import fields
from odoo.tests import new_test_user


def key():
    return secrets.token_hex(12)


def bind(cls, user=None, store=None, session_key=None):
    user = user or cls.users['stock']
    access = cls.root['ydental.access.service'].with_user(user)
    session = access._session_for_key(session_key or key())
    access = access._bind(session)
    access._switch((store or cls.stores[0]).id)
    return access._bind(session).env['ydental.inventory.service']


def setup(cls):
    cls.root = cls.env['base'].sudo().env
    root = cls.root
    cls.company2 = root['res.company'].create({'name': 'S07 Synthetic Legal B ' + key()[:6]})
    cls.stores = root['ydental.access.store'].create([
        {'name': 'S07 Synthetic A ' + key()[:6], 'company_id': root.company.id, 'ydental_timezone': 'Asia/Shanghai'},
        {'name': 'S07 Synthetic B ' + key()[:6], 'company_id': root.company.id, 'ydental_timezone': 'UTC'},
        {'name': 'S07 Synthetic Legal C ' + key()[:6], 'company_id': cls.company2.id, 'ydental_timezone': 'America/New_York'}])
    cls.users = {}
    for role in ('manager', 'stock', 'stock2', 'reader', 'doctor', 'pharmacy', 'price', 'none', 'catalog'):
        groups = 'ydental_base.ydental_base_group_user'
        if role in ('manager', 'catalog'): groups += ',ydental_access.ydental_group_manager'
        if role == 'stock2': groups += ',stock.group_stock_manager'
        cls.users[role] = new_test_user(root, name='S07 Synthetic ' + role, login='s07_' + role + '_' + key()[:8],
            password='s07-test-password', groups=groups, company_ids=[fields.Command.set((root.company | cls.company2).ids)])
    a = root['ydental.access.service'].with_user(cls.users['manager'])
    cls.admin = a._bind(a._session_for_key(key()))
    for user in cls.users.values():
        for store in cls.stores: cls.admin._join(user.id, store.id)
    for store in cls.stores:
        cls.admin._grant(cls.users['manager'].id, store.id, {'warehouse': 'write', 'export': 'write', 'price': 'write'})
        for role in ('stock', 'stock2'): cls.admin._grant(cls.users[role].id, store.id, {'warehouse': 'write'})
        cls.admin._grant(cls.users['reader'].id, store.id, {'warehouse': 'read'})
        cls.admin._grant(cls.users['doctor'].id, store.id, {'medical': 'write'})
        cls.admin._grant(cls.users['pharmacy'].id, store.id, {'pharmacy': 'write'})
        cls.admin._grant(cls.users['price'].id, store.id, {'price': 'write'})
    cls.group = bind(cls, cls.users['manager']); cls.stock = bind(cls)
    cls.uom = root.ref('uom.product_uom_unit')
    cls.pack = root['uom.uom'].create({'name': 'S07 Synthetic pack of ten', 'relative_uom_id': cls.uom.id, 'relative_factor': 10})
    for n, store in enumerate(cls.stores): bind(cls, store=store)._operate('setup', {'code': 'T'+str(store.id)[-4:]}, key())
    cls.products, cls.lots = {}, {}
    for kind in ('medicine', 'material', 'prosthesis'):
        product = cls.group._operate('product', {'code': 'S07-'+key(), 'name': 'S07 '+kind, 'kind': kind,
            'stock_uom_id': cls.uom.id, 'issue_uom_id': cls.pack.id, 'step': 0.01, 'specification': 'Synthetic specification'}, key())
        cls.products[kind] = product['id']
        cls.lots[kind] = cls.stock._operate('lot', {'product_id': product['id'], 'name': 'S07-'+key(),
            'expiration': fields.Datetime.to_string(fields.Datetime.now()+timedelta(days=45))}, key())['id']


def op(cls, operation, args=None, service=None, request_key=None, **kwargs):
    return (service if service is not None else cls.stock)._operate(operation, args or kwargs, request_key or key())


def receive(cls, quantity=10, lot=None):
    return op(cls, 'receive', lot_id=lot or cls.lots['medicine'], quantity=quantity, uom_id=cls.uom.id,
        source_key=key(), reason='Synthetic real receipt evidence')


def issue(cls, quantity=3, lot=None, request_key=None, source_key=None, service=None):
    return op(cls, 'issue', service=service, request_key=request_key, lot_id=lot or cls.lots['medicine'], quantity=quantity,
        uom_id=cls.uom.id, source_key=source_key or key(), reason='Synthetic actual replenishment issue evidence')


def quantity(cls, lot=None, quarantine=False, store=None):
    s = bind(cls, store=store) if store else cls.stock
    store = s._access()
    lot = s._lot(lot or cls.lots['medicine'], store)
    config = s._config(store)
    return s._quantity(lot, config.ydental_quarantine_id if quarantine else s._location(config, lot.product_id))
