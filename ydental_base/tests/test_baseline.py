from odoo.tests import HttpCase, new_test_user
from odoo.tools import mute_logger


class TestYDentalBaseline(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dental_user = new_test_user(
            cls.env, login='p00_dental', groups='ydental_base.ydental_base_group_user',
        )
        cls.other_user = new_test_user(cls.env, login='p00_other')
        cls.portal_user = new_test_user(
            cls.env, login='p00_portal', groups='base.group_portal',
        )

    def test_application_entry(self):
        self.authenticate(self.dental_user.login, self.dental_user.login)
        response = self.url_open('/ydental')
        self.assertEqual(response.status_code, 200)
        self.assertIn('YDental 项目基线已就绪。', response.text)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        menus = self.url_open('/web/webclient/load_menus').json()
        menu_id = str(self.env.ref('ydental_base.ydental_base_menu_root').id)
        self.assertIn(menu_id, menus)
        self.assertEqual(menus[menu_id]['name'], '牙科')
        action = self.env.ref('ydental_base.ydental_base_action')
        self.assertEqual(action.url, '/ydental')

    def test_internal_user_denied(self):
        self.authenticate(self.other_user.login, self.other_user.login)
        with mute_logger('odoo.http'):
            self.assertEqual(self.url_open('/ydental').status_code, 403)
        menus = self.url_open('/web/webclient/load_menus').json()
        menu_id = str(self.env.ref('ydental_base.ydental_base_menu_root').id)
        self.assertNotIn(menu_id, menus)

    def test_portal_user_denied(self):
        self.authenticate(self.portal_user.login, self.portal_user.login)
        with mute_logger('odoo.http'):
            self.assertEqual(self.url_open('/ydental').status_code, 403)

    def test_anonymous_requires_login(self):
        response = self.url_open('/ydental', allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn('/web/login', response.headers['Location'])

    def test_upgrade_keeps_single_entry_and_safe_demo(self):
        self.assertEqual(self.env['ir.ui.menu'].search_count([
            ('action', '=', 'ir.actions.act_url,%s' % self.env.ref(
                'ydental_base.ydental_base_action',
            ).id),
        ]), 1)
        demo_user = self.env.ref('ydental_base.user_demo', raise_if_not_found=False)
        if demo_user:
            self.assertFalse(demo_user.active)
            self.assertFalse(demo_user.has_group('base.group_system'))
