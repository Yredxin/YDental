"""LC2 compatibility and audit-contract tests; framework transactions own rollback."""
import os
import logging
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http.dispatcher import serialize_exception
from odoo.tests import HttpCase, TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger

from odoo.addons.ydental_access.diagnostic_errors import native_error
from odoo.addons.ydental_access.diagnostics import classify_error, context_scope, current_context, safe_exception_chain


@tagged('post_install', '-at_install', 's10_lc2')
class TestLogCloseout(TransactionCase):
    def test_native_error_serialization_exact_type_arguments_and_translation(self):
        for lang in ('en_US', 'zh_CN'):
            env = self.env(context=dict(self.env.context, lang=lang))
            self.assertTrue(env['res.lang'].with_context(active_test=False).search([('code', '=', lang)]).active,
                            'GPR-01 requires both actual installed languages, not English fallback')
            with self.assertRaises(AccessError) as caught:
                env['ydental.access.audit'].browse().write({'ydental_reason': 'synthetic denied write'})
            message = caught.exception.args[0]
            self.assertEqual(message, '审计事件不可修改。' if lang == 'zh_CN' else 'Audit events cannot be changed.')
            for error_type in (AccessError, UserError, ValidationError):
                with self.subTest(lang=lang, error=error_type.__name__):
                    error = native_error(error_type, message, 'AUTHZ_DENIED')
                    original = error_type(message)
                    self.assertIs(type(error), error_type)
                    self.assertEqual(error.args, original.args)
                    serialized, before = serialize_exception(error), serialize_exception(original)
                    self.assertEqual(serialized['name'], 'odoo.exceptions.' + error_type.__name__)
                    self.assertEqual(serialized['name'], before['name'])
                    self.assertEqual(serialized['arguments'], before['arguments'])
                    self.assertEqual(serialized['message'], before['message'])
                    self.assertEqual(serialized['context'], before['context'])
                    self.assertNotIn('diagnostic_code', serialized['context'])

    def test_service_type_error_is_not_localized_business_rejection(self):
        for error in (TypeError('synthetic'), KeyError('synthetic'), NameError('synthetic')):
            self.assertEqual(classify_error(error, 'business.start')[0], 'APPLICATION_ERROR')
        self.assertEqual(classify_error(ValueError('synthetic'), 'request.parse'),
                         ('BUSINESS_REJECTION', 'INPUT_PARSE_ERROR'))

    def test_gpr02_chained_native_exception_keeps_framework_identity(self):
        identity = (self.env.uid, self.env.su, self.env.transaction.default_env)
        try:
            try:
                raise LookupError('synthetic secret cause')
            except LookupError as cause:
                raise native_error(AccessError, 'Audit events cannot be changed.', 'AUTHZ_DENIED') from cause
        except AccessError as error:
            before = (type(error), error.args, error.__cause__, error.__context__, error.__traceback__)
            chain = safe_exception_chain(error)
            self.assertEqual([node['exception_type'] for node in chain['nodes']], ['AccessError', 'LookupError'])
            self.assertEqual(chain['nodes'][0]['link_type'], 'cause')
            self.assertEqual(chain['nodes'][1]['exception_module'], 'builtins')
            self.assertEqual((type(error), error.args, error.__cause__, error.__context__, error.__traceback__), before)
            self.assertEqual(serialize_exception(error)['name'], 'odoo.exceptions.AccessError')
        self.assertEqual((self.env.uid, self.env.su, self.env.transaction.default_env), identity)

    def test_mandatory_business_audit_failure_propagates(self):
        audit_type = type(self.env['ydental.access.audit'])
        with patch.object(audit_type, 'create', side_effect=RuntimeError('synthetic mandatory audit failure')):
            with self.assertRaisesRegex(RuntimeError, 'synthetic mandatory audit failure'):
                self.env['ydental.access.service']._audit('lc2.synthetic', 'personnel', self.env.user)

    def test_context_restores_and_does_not_change_environment_identity(self):
        self.assertEqual(logging.getLogger('odoo.http.server').getEffectiveLevel(), logging.CRITICAL)
        self.assertEqual(logging.getLogger('ydental.events').getEffectiveLevel(), logging.INFO)
        identity = (self.env.uid, self.env.su, self.env.transaction.default_env)
        previous = current_context()
        with context_scope(case_id='L06', actor_id=self.env.uid, effective_uid=self.env.uid):
            self.assertEqual(current_context()['case_id'], 'L06')
            self.assertEqual((self.env.uid, self.env.su, self.env.transaction.default_env), identity)
        self.assertEqual(current_context(), previous)


@tagged('post_install', '-at_install', 's10_lc2')
class TestLogCloseoutHTTP(HttpCase):
    def url_open(self, url, *args, allow_redirects=False, **kwargs):
        # authenticate() in this fixed core seeds a framework session locally;
        # every actual HTTP call here is explicit and never follows redirects.
        from s10_lc2_targets import PackageBudget
        budget_directory = os.environ.get('YDENTAL_LC2_BUDGET_DIR')
        if not budget_directory:
            raise RuntimeError('LC2_HTTP_TEST_REQUIRES_APPROVED_BUDGET')
        if allow_redirects:
            raise RuntimeError('LC2_HTTP_TEST_AUTO_REDIRECT_FORBIDDEN')
        PackageBudget(budget_directory).consume('http')
        return super().url_open(url, *args, allow_redirects=False, **kwargs)

    def test_actual_rpc_preserves_native_access_error_name_and_arguments(self):
        user = new_test_user(self.env, login='lc2_rpc_user', groups='base.group_user')
        audit = self.env['ydental.access.audit'].sudo().create({
            'ydental_user_id': user.id, 'ydental_event': 'lc2.synthetic',
            'ydental_category': 'personnel', 'ydental_target_model': 'res.users',
            'ydental_target_id': user.id, 'ydental_result': 'accepted', 'ydental_source': 'lc2_fixture',
        })
        self.authenticate(user.login, user.login)
        with mute_logger('odoo.http'):
            response = self.url_open('/web/dataset/call_kw/ydental.access.audit.write',
                                     data='{"jsonrpc":"2.0","method":"call","id":1,"params":'
                                          '{"model":"ydental.access.audit","method":"write","args":'
                                          '[[' + str(audit.id) + '],{"ydental_reason":"synthetic tamper"}],"kwargs":{}}}',
                                     headers={'Content-Type': 'application/json', 'X-YDental-Case-ID': 'L03',
                                              'X-YDental-Operation-Ref': 'lc2-framework-native-audit-denial'})
        self.assertEqual(response.status_code, 200)
        value = response.json()
        self.assertNotIn('result', value)
        self.assertEqual(value['error']['data']['name'], 'odoo.exceptions.AccessError')
        self.assertEqual(value['error']['data']['arguments'], ['Audit events cannot be changed.'])
        self.assertEqual(value['error']['data']['context'], {})
        self.assertFalse(audit.ydental_reason)
