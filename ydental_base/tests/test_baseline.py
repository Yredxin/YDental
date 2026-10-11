import io

from odoo.tests import HttpCase, new_test_user
from odoo.tools import mute_logger
from odoo.tools.pdf import PdfFileReader


class TestYDentalBaseline(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].set_str('report.url', cls.base_url())
        cls.env['ir.config_parameter'].set_str('web.base.url', cls.base_url())
        cls.dental_user = new_test_user(
            cls.env, login='s00b_dental', groups='ydental_base.ydental_base_group_user',
            lang='en_US',
        )
        cls.chinese_user = new_test_user(
            cls.env, login='s00b_chinese', groups='ydental_base.ydental_base_group_user',
            lang='zh_CN',
        )
        cls.other_user = new_test_user(cls.env, login='s00b_other')
        cls.portal_user = new_test_user(
            cls.env, login='s00b_portal', groups='base.group_portal',
        )

    def test_application_entry(self):
        self.authenticate(self.dental_user.login, self.dental_user.login)
        response = self.url_open('/ydental')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Welcome to YDental.', response.text)
        self.assertNotIn('P00', response.text)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        menus = self.url_open('/web/webclient/load_menus').json()
        menu_id = str(self.env.ref('ydental_base.ydental_base_menu_root').id)
        self.assertIn(menu_id, menus)
        self.assertEqual(menus[menu_id]['name'], 'Dental')
        self.assertEqual(self.env.ref('ydental_base.ydental_base_action').url, '/ydental')

    def test_chinese_entry(self):
        self.authenticate(self.chinese_user.login, self.chinese_user.login)
        response = self.url_open('/ydental')
        self.assertEqual(response.status_code, 200)
        self.assertIn('欢迎使用 YDental。', response.text)
        menus = self.url_open('/web/webclient/load_menus').json()
        menu_id = str(self.env.ref('ydental_base.ydental_base_menu_root').id)
        self.assertEqual(menus[menu_id]['name'], '牙科')

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
        for path in ('/ydental', '/ydental/sample/a4', '/ydental/sample/narrow',
                     '/report/pdf/ydental_base.ydental_sample_a4'):
            with self.subTest(path=path):
                response = self.url_open(path, allow_redirects=False)
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

    def test_real_chinese_pdf_downloads(self):
        self.authenticate(self.chinese_user.login, self.chinese_user.login)
        for paper, width, height in (('a4', 210, 297), ('narrow', 80, 200)):
            with self.subTest(paper=paper):
                response = self.url_open('/ydental/sample/' + paper, timeout=45)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers['Content-Type'], 'application/pdf')
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
                self.assertTrue(response.content.startswith(b'%PDF-'))
                reader = PdfFileReader(io.BytesIO(response.content))
                self.assertEqual(len(reader.pages), 1)
                page = reader.pages[0]
                self.assertAlmostEqual(float(page.mediabox.width) * 25.4 / 72, width, delta=1)
                self.assertAlmostEqual(float(page.mediabox.height) * 25.4 / 72, height, delta=1)

    def test_pdf_denied_on_custom_and_native_routes(self):
        for user in (self.other_user, self.portal_user):
            self.authenticate(user.login, user.login)
            for paper in ('a4', 'narrow'):
                paths = (
                    '/ydental/sample/' + paper,
                    '/report/pdf/ydental_base.ydental_sample_' + paper,
                    '/report/html/ydental_base.ydental_sample_' + paper,
                )
                for path in paths:
                    with self.subTest(user=user.login, path=path), mute_logger('odoo.http'):
                        response = self.url_open(path)
                        self.assertEqual(response.status_code, 403)
                        self.assertFalse(response.content.startswith(b'%PDF-'))

    def test_revoked_group_denied_next_request(self):
        self.authenticate(self.dental_user.login, self.dental_user.login)
        self.assertEqual(self.url_open('/ydental').status_code, 200)
        group = self.env.ref('ydental_base.ydental_base_group_user')
        self.dental_user.write({'group_ids': [(3, group.id)]})
        with mute_logger('odoo.http'):
            self.assertEqual(self.url_open('/ydental').status_code, 403)
            self.assertEqual(self.url_open('/ydental/sample/a4').status_code, 403)
