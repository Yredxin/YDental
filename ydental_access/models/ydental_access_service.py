import hashlib
import json
import logging

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from ..diagnostics import emit_event
from .constants import Binding, CATEGORIES, GROUP_MANAGER, RANK, SYSTEM_MANAGER


_logger = logging.getLogger(__name__)


class YDentalAccessService(models.AbstractModel):
    _name = 'ydental.access.service'
    _description = 'YDental trusted authorization and lifecycle service'

    def _denial(self, action):
        # Security rejection survives a rolled-back business transaction. Never
        # log request bodies, credentials, clinical text or a denied source ID.
        _logger.info('YDental security rejection actor=%s action=%s result=denied', self.env.uid, action)
        emit_event('security.rejected', component='access', operation=action,
                   actor_id=self.env.uid, effective_uid=self.env.uid, su_flag=self.env.su,
                   outcome='denied', error_class='BUSINESS_REJECTION', error_code='AUTHZ_DENIED')

    def _require_internal(self):
        if not self.env.user.active or not self.env.user._is_internal() or not self.env.user.has_group(
            'ydental_base.ydental_base_group_user',
        ):
            raise AccessError(self.env._('access_denied: YDental internal access is required.'))

    def _is_group_manager(self):
        return self.env.su or self.env.user.has_group(GROUP_MANAGER)

    def _validate_levels(self, levels):
        if not isinstance(levels, dict) or set(levels) - dict(CATEGORIES).keys() or any(
            level not in RANK for level in levels.values()
        ):
            raise ValidationError(self.env._('Unknown permission category or level.'))

    def _session_for_key(self, key):
        """key is supplied only by the HTTP adapter from the server session."""
        self._require_internal()
        digest = hashlib.sha256(key.encode()).hexdigest()
        Session = self.env['ydental.access.session'].sudo()
        # Serialize initialization across concurrent first requests of one user.
        self._lock_user(self.env.uid)
        session = Session.search([('ydental_key_hash', '=', digest)], limit=1)
        if not session:
            session = Session.create({'ydental_key_hash': digest, 'ydental_user_id': self.env.uid})
            self._audit('login.scope', 'personnel', session, source='authenticated_session')
            # The hook is server code, not a request context hint. Consume it
            # exactly once; an invalid suggestion leaves the session unselected.
            store_id = self._get_default_store_id()
            if type(store_id) is int and store_id > 0:
                store = self.env['ydental.access.store'].sudo().browse(store_id).exists()
                member = self._membership(self.env.uid, store_id)
                if store and store.active and member and member.ydental_employee_id.active:
                    self._bind(session)._switch(store_id)
        if session.ydental_user_id.id != self.env.uid:
            raise AccessError(self.env._('access_denied: Invalid login scope.'))
        return session

    def _existing_session_for_key(self, key):
        self._require_internal()
        return self.env['ydental.access.session'].sudo().search([
            ('ydental_key_hash', '=', hashlib.sha256(key.encode()).hexdigest()),
            ('ydental_user_id', '=', self.env.uid),
        ], limit=1)

    def _create_account(self, name, login, store_id):
        self._check_personnel(store_id)
        if not isinstance(name, str) or not isinstance(login, str) or not name.strip() or not login.strip():
            raise ValidationError(self.env._('Name and login are required.'))
        if len(name) > 100 or len(login) > 200:
            raise ValidationError(self.env._('Name or login is too long.'))
        Users = self.env['res.users'].sudo().with_context(no_reset_password=True)
        user = Users.with_context(active_test=False).search([('login', '=', login.strip())], limit=1)
        if user and (not user.active or not user._is_internal()):
            raise AccessError(self.env._('access_denied: Select an active internal account.'))
        if not user:
            store = self.env['ydental.access.store'].sudo().browse(store_id).exists()
            if not store or not store.active:
                raise AccessError(self.env._('access_denied: Select an active store.'))
            user = Users.create({
                'name': name.strip(), 'login': login.strip(), 'email': login.strip(),
                'company_id': store.company_id.id,
                'company_ids': [fields.Command.set([store.company_id.id])],
                'group_ids': [fields.Command.set([
                    self.env.ref('ydental_base.ydental_base_group_user').id,
                ])],
            })
            self._audit('account.create', 'personnel', user, store_id, after={'active': True})
        self._join(user.id, store_id)
        return {'user_id': user.id, 'result': 'accepted'}

    def _create_store(self, name, company_id, timezone):
        self._scope(write=True)
        if not self._is_group_manager() or type(company_id) is not int or company_id not in self.env.user.company_ids.ids:
            raise AccessError(self.env._('access_denied: Group administration within allowed companies is required.'))
        if not isinstance(name, str) or not name.strip() or len(name) > 100:
            raise ValidationError(self.env._('A valid store name is required.'))
        store = self.env['ydental.access.store'].create({
            'name': name.strip(), 'company_id': company_id, 'ydental_timezone': timezone,
        })
        self._join(self.env.uid, store.id)
        return {'result': 'accepted', 'store_id': store.id}

    def _update_profile(self, user_id, job_title, capability_ids):
        self._scope(write=True)
        if not self._is_group_manager() or not isinstance(job_title, str) or len(job_title) > 100 or not isinstance(
            capability_ids, list,
        ) or any(type(i) is not int for i in capability_ids):
            raise AccessError(self.env._('access_denied: Group administration and valid common fields are required.'))
        self._lock_user(user_id)
        user = self.env['res.users'].sudo().browse(user_id).exists()
        capabilities = self.env['ydental.access.capability'].sudo().browse(capability_ids).exists()
        if not user or len(capabilities) != len(set(capability_ids)) or not all(capabilities.mapped('active')):
            raise ValidationError(self.env._('Select an account and active capabilities.'))
        self._check_user_company_scope(user)
        old = {'job_title': user.ydental_job_title, 'capability_ids': user.ydental_capability_ids.ids}
        user.write({'ydental_job_title': job_title, 'ydental_capability_ids': [fields.Command.set(capability_ids)]})
        self._audit('profile.change', 'personnel', user, before=old,
                    after={'job_title': job_title, 'capability_ids': capability_ids})
        return {'result': 'accepted'}

    def _set_manager(self, user_id, store_id, appointed):
        self._scope(write=True)
        if not self._is_group_manager() or type(appointed) is not bool:
            raise AccessError(self.env._('access_denied: Manager appointments require group administration.'))
        policy = self.env['ir.config_parameter'].sudo().get_str('ydental_access.manager_policy')
        if policy != 'group_with_replacement':
            raise UserError(self.env._('Manager appointment policy has not been approved and configured.'))
        self._check_personnel(store_id, user_id)
        self.env.cr.execute('SELECT id FROM ydental_access_store WHERE id=%s FOR UPDATE', [store_id])
        member = self._membership(user_id, store_id)
        if not member:
            raise AccessError(self.env._('access_denied: An active target membership is required.'))
        member.invalidate_recordset()
        if not appointed and member.ydental_is_manager:
            others = self.env['ydental.access.membership'].sudo().search_count([
                ('ydental_store_id', '=', store_id), ('ydental_is_manager', '=', True),
                ('id', '!=', member.id), ('active', '=', True),
                ('ydental_user_id.active', '=', True), ('ydental_employee_id.active', '=', True),
            ])
            if not others:
                raise UserError(self.env._('Appoint a replacement before removing the last active store manager.'))
        old = member.ydental_is_manager
        member.write({'ydental_is_manager': appointed})
        if old != appointed:
            self._audit('manager.appointment', 'personnel', member, store_id,
                        before={'manager': old}, after={'manager': appointed}, source='approved_manager_policy')
        return {'result': 'accepted'}

    def _configure_policy(self, manager_policy, password_minlength, inactivity_minutes, require_mfa):
        self._scope(write=True)
        if not self.env.user.has_group(SYSTEM_MANAGER) or manager_policy not in ('', 'group_with_replacement') or (
            type(password_minlength) is not int or not 8 <= password_minlength <= 128 or
            type(inactivity_minutes) is not int or not 1 <= inactivity_minutes <= 1440 or type(require_mfa) is not bool
        ):
            raise AccessError(self.env._('access_denied: Technical configuration and explicit valid parameters are required.'))
        params = self.env['ir.config_parameter'].sudo()
        params.set_str('ydental_access.manager_policy', manager_policy)
        params.set_int('auth_password_policy.minlength', password_minlength)
        params.set_str('auth_totp.policy', 'employee_required' if require_mfa else '')
        self.env.ref('ydental_base.ydental_base_group_user').sudo().write({
            'lock_timeout_inactivity': inactivity_minutes, 'lock_timeout_inactivity_mfa': require_mfa,
        })
        self._audit('security.policy', 'personnel', self.env.user,
                    after={'manager_policy': manager_policy, 'password_minlength': password_minlength,
                           'inactivity_minutes': inactivity_minutes, 'require_mfa': require_mfa}, source='explicit_configuration')
        return {'result': 'accepted'}

    def _request_invitation(self, user_id, store_id):
        self._check_personnel(store_id, user_id)
        member = self._membership(user_id, store_id)
        if not member:
            raise AccessError(self.env._('access_denied: An active target membership is required.'))
        user = member.ydental_user_id
        if (user.has_group(GROUP_MANAGER) or user.has_group(SYSTEM_MANAGER) or user.has_group('base.group_system')) and not self.env.user.has_group(SYSTEM_MANAGER):
            raise AccessError(self.env._('access_denied: Privileged account resets require technical configuration.'))
        user.with_context(create_user=True).action_reset_password()
        self._audit('account.invitation', 'personnel', user, store_id,
                    after={'result': 'accepted'}, source='native_invitation_request')
        return {'result': 'accepted', 'delivery': 'not_verified'}

    def _get_sources(self):
        """Installed upper modules register literal code-to-model mappings."""
        return {}

    def _dashboard(self):
        session = self._scope()
        members = self.env['ydental.access.membership'].sudo().search([
            ('ydental_user_id', '=', self.env.uid), ('active', '=', True),
            ('ydental_store_id.active', '=', True), ('ydental_employee_id.active', '=', True),
        ])
        stores = members.mapped('ydental_store_id')
        store = session.ydental_store_id
        own = members.filtered(lambda m: m.ydental_store_id == store)
        can_manage = bool(own and (own.ydental_is_manager or self._levels(own)['personnel'] == 'write')) or self._is_group_manager()
        roster = []
        if store and can_manage:
            for member in self.env['ydental.access.membership'].sudo().search([('ydental_store_id', '=', store.id)]):
                roster.append({'id': member.id, 'user_id': member.ydental_user_id.id,
                               'name': member.ydental_user_id.name, 'employee_id': member.ydental_employee_id.id,
                               'manager': member.ydental_is_manager, 'levels': self._levels(member)})
        return {'stores': [{'id': s.id, 'name': s.name} for s in stores],
                'store_id': store.id, 'store_name': store.name if own else '',
                'revision': session.ydental_revision, 'can_manage': can_manage,
                'execution_store_id': self._get_execution_store_id(), 'roster': roster,
                'categories': self.env['ydental.access.grant']._fields['ydental_category']._description_selection(self.env),
                'is_group_manager': self._is_group_manager(),
                'is_system_manager': self.env.user.has_group(SYSTEM_MANAGER),
                'capabilities': self.env['ydental.access.capability'].sudo().search([]).read(['name']) if self._is_group_manager() else [],
                'templates': self.env['ydental.access.template'].sudo().search([('active', '=', True)]).read(['name'])
                if can_manage else [], 'audits': self._audit_rows()}

    def _bind(self, session, revision=None):
        self._require_internal()
        session.ensure_one()
        if session.sudo().ydental_user_id.id != self.env.uid:
            raise AccessError(self.env._('access_denied: Invalid login scope.'))
        binding = Binding(self.env.uid, session.id, session.sudo().ydental_revision)
        if revision is not None and revision != binding.revision:
            raise UserError(self.env._('version_conflict: The store changed. Refresh this page.'))
        return self.with_context(ydental_binding=binding)

    def _scope(self, write=False):
        self._require_internal()
        binding = self.env.context.get('ydental_binding')
        if not isinstance(binding, Binding) or binding.user_id != self.env.uid:
            self._denial('scope')
            raise AccessError(self.env._('access_denied: A server-bound login scope is required.'))
        session = self.env['ydental.access.session'].sudo().browse(binding.session_id).exists()
        if write:
            # Transaction lock closes the old-tab/switch race. A retry rebinds.
            self.env.cr.execute('SELECT id FROM ydental_access_session WHERE id=%s FOR UPDATE', [session.id])
            session.invalidate_recordset()
        if not session or session.ydental_user_id.id != self.env.uid:
            raise AccessError(self.env._('access_denied: Invalid login scope.'))
        if session.ydental_revision != binding.revision:
            raise UserError(self.env._('version_conflict: The store changed. Refresh this page.'))
        return session

    def _lock_user(self, user_id):
        # Transaction advisory lock protects grant/lifecycle read-modify-write.
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [25001, user_id])

    def _membership(self, user_id, store_id, active=True):
        domain = [('ydental_user_id', '=', user_id), ('ydental_store_id', '=', store_id)]
        if active:
            domain.append(('active', '=', True))
        return self.env['ydental.access.membership'].sudo().with_context(active_test=False).search(domain, limit=1)

    def _levels(self, membership):
        levels = dict.fromkeys(dict(CATEGORIES), 'none')
        for grant in self.env['ydental.access.grant'].sudo().search([
            ('ydental_membership_id', '=', membership.id),
        ]):
            levels[grant.ydental_category] = grant.ydental_level
        return levels

    def _get_care_domain(self, model_name):
        """Default deny. Upper modules must validate the patient/task server-side.

        Never derive this domain from a client purpose, record ID or context
        dictionary. S01 supplies no patient/task authorizer.
        """
        return fields.Domain.FALSE

    def _user_company_ids(self, users):
        """All companies affected by account-wide staff lifecycle changes."""
        users = users.sudo().with_context(active_test=False)
        employees = self.env['hr.employee'].sudo().with_context(active_test=False).search([
            ('user_id', 'in', users.ids),
        ])
        members = self.env['ydental.access.membership'].sudo().with_context(active_test=False).search([
            ('ydental_user_id', 'in', users.ids),
        ])
        return set(users.company_ids.ids + users.company_id.ids + employees.company_id.ids +
                   members.ydental_store_id.company_id.ids)

    def _check_user_company_scope(self, users):
        if not self.env.su and not self._user_company_ids(users) <= set(self.env.user.company_ids.ids):
            raise AccessError(self.env._('access_denied: Group administration within allowed companies is required.'))

    def _get_execution_store_id(self):
        """S06 overrides from its authoritative execution lease, never context."""
        return False

    def _get_default_store_id(self):
        """S03 may propose a store; switch still checks current membership."""
        return False

    def _check(self, category, level='read', store_id=None, write=False):
        if category not in dict(CATEGORIES) or level not in RANK:
            raise AccessError(self.env._('access_denied: Invalid authorization action.'))
        session = self._scope(write=write)
        store_id = store_id or session.ydental_store_id.id
        if not store_id or not self.env['ydental.access.store'].sudo().browse(store_id).active:
            raise AccessError(self.env._('access_denied: Select an active store.'))
        membership = self._membership(self.env.uid, store_id)
        if not membership or not membership.ydental_employee_id.active:
            raise AccessError(self.env._('access_denied: Active store membership is required.'))
        if RANK[self._levels(membership)[category]] < RANK[level]:
            raise AccessError(self.env._('access_denied: This business permission is required.'))
        if write and self._get_execution_store_id() not in (False, store_id):
            raise AccessError(self.env._('access_denied: Execution in another store blocks manual writes.'))
        return membership

    def _audit_values(self, event, category, target, store_id=False, before=None, after=None,
                      result='accepted', reason=False, source='interactive'):
        """Private preparation, containing only documented nonsensitive metadata."""
        return {
            'ydental_user_id': self.env.uid, 'ydental_store_id': store_id,
            'ydental_event': event, 'ydental_category': category,
            'ydental_target_model': target._name, 'ydental_target_id': target.id,
            'ydental_result': result, 'ydental_reason': reason,
            'ydental_before': before, 'ydental_after': after, 'ydental_source': source,
        }

    def _audit(self, event, category, target, store_id=False, before=None, after=None,
               result='accepted', reason=False, source='interactive'):
        audit = self.env['ydental.access.audit'].sudo().create(self._audit_values(
            event, category, target, store_id, before, after, result, reason, source,
        ))
        emit_event('audit.created', component='access.audit', operation=event,
                   actor_id=self.env.uid, effective_uid=audit.env.uid, su_flag=audit.env.su,
                   store_id=store_id or None, audit_ref=audit.id,
                   transaction_phase='IN_TRANSACTION', commit_observation='NOT_OBSERVED')
        return audit

    def _switch(self, store_id):
        session = self._scope(write=True)
        member = self._membership(self.env.uid, store_id)
        store = self.env['ydental.access.store'].sudo().browse(store_id).exists()
        if not store or not store.active or not member or not member.ydental_employee_id.active:
            raise AccessError(self.env._('access_denied: Active store membership is required.'))
        old = session.ydental_store_id.id
        if old == store_id:
            return session.ydental_revision
        session.write({'ydental_store_id': store_id, 'ydental_revision': session.ydental_revision + 1})
        self._audit('store.switch', 'personnel', session, store_id,
                    before={'store_id': old}, after={'store_id': store_id})
        return session.ydental_revision

    def _check_personnel(self, store_id, target_user_id=None, levels=None):
        self._scope(write=True)
        if self._get_execution_store_id() not in (False, store_id):
            raise AccessError(self.env._('access_denied: Execution in another store blocks manual writes.'))
        if self._is_group_manager():
            store = self.env['ydental.access.store'].sudo().browse(store_id).exists()
            if not store or not self.env.su and store.company_id not in self.env.user.company_ids:
                raise AccessError(self.env._('access_denied: Group administration within allowed companies is required.'))
            return
        own = self._membership(self.env.uid, store_id)
        if not own or not own.ydental_employee_id.active:
            raise AccessError(self.env._('access_denied: Personnel authorization is required.'))
        own_levels = self._levels(own)
        if own.ydental_is_manager:
            return
        if own_levels['personnel'] != 'write':
            raise AccessError(self.env._('access_denied: Personnel authorization is required.'))
        if target_user_id == self.env.uid:
            raise AccessError(self.env._('access_denied: Personnel administrators cannot change themselves.'))
        if levels is not None and any(RANK[v] > RANK[own_levels[k]] for k, v in levels.items()):
            raise AccessError(self.env._('access_denied: A grant cannot exceed your own level.'))

    def _grant(self, user_id, store_id, levels, source='manual'):
        self._validate_levels(levels)
        self._check_personnel(store_id, user_id, levels)
        self._lock_user(user_id)
        membership = self._membership(user_id, store_id)
        if not membership or not membership.ydental_user_id.active or not membership.ydental_employee_id.active:
            raise AccessError(self.env._('access_denied: An active target membership is required.'))
        if membership.ydental_is_manager and not self._is_group_manager() and not self._membership(
            self.env.uid, store_id,
        ).ydental_is_manager:
            raise AccessError(self.env._('access_denied: Store manager assignments are independently protected.'))
        old = self._levels(membership)
        Grant = self.env['ydental.access.grant'].sudo()
        existing = {g.ydental_category: g for g in Grant.search([
            ('ydental_membership_id', '=', membership.id),
        ])}
        creates = []
        audit_values = []
        updates = {}
        for category, level in levels.items():
            if old[category] == level:
                continue
            if category in existing:
                updates[level] = updates.get(level, Grant.browse()) | existing[category]
            else:
                creates.append({'ydental_membership_id': membership.id,
                                'ydental_category': category, 'ydental_level': level})
            audit_values.append(self._audit_values('authorization.change', 'personnel', membership, store_id,
                                                  before={category: old[category]}, after={category: level}, source=source))
        for level, grants in updates.items():
            grants.write({'ydental_level': level})
        if creates:
            Grant.create(creates)
        if audit_values:
            self.env['ydental.access.audit'].sudo().create(audit_values)
        return membership.id

    def _template_preview(self, template_id, targets):
        if not isinstance(targets, list) or not 1 <= len(targets) <= 50 or any(
            not isinstance(t, list) or len(t) != 2 or any(type(i) is not int for i in t)
            for t in targets
        ) or len({tuple(t) for t in targets}) != len(targets):
            raise ValidationError(self.env._('Select between one and fifty distinct account/store targets.'))
        template = self.env['ydental.access.template'].sudo().browse(template_id).exists()
        if not template or not template.active:
            raise AccessError(self.env._('access_denied: An active template is required.'))
        template._check_levels()
        desired = dict.fromkeys(dict(CATEGORIES), 'none') | template.ydental_levels
        rows = []
        for user_id, store_id in sorted(targets):
            self._check_personnel(store_id, user_id, desired)
            self._lock_user(user_id)
            member = self._membership(user_id, store_id)
            if not member or not member.ydental_user_id.active or not member.ydental_employee_id.active:
                raise AccessError(self.env._('access_denied: An active target membership is required.'))
            own = self._membership(self.env.uid, store_id)
            if member.ydental_is_manager and not self._is_group_manager() and not (own and own.ydental_is_manager):
                raise AccessError(self.env._('access_denied: Store manager assignments are independently protected.'))
            rows.append({'user_id': user_id, 'store_id': store_id,
                         'before': self._levels(member), 'after': desired})
        receipt = hashlib.sha256(json.dumps(
            {'template_id': template.id, 'rows': rows}, sort_keys=True,
        ).encode()).hexdigest()
        return {'template_id': template.id, 'rows': rows, 'receipt': receipt}

    def _apply_template(self, template_id, targets, receipt):
        preview = self._template_preview(template_id, targets)
        if preview['receipt'] != receipt:
            raise UserError(self.env._('version_conflict: Permissions or the template changed. Preview again.'))
        # Validate the complete batch before any mutation; transaction is all-or-nothing.
        for row in preview['rows']:
            self._grant(row['user_id'], row['store_id'], row['after'], source='template:%s' % template_id)
        self._audit('template.apply', 'personnel', self.env['ydental.access.template'].browse(template_id),
                    after={'targets': targets}, source='confirmed_preview')
        return {'result': 'accepted', 'targets': targets}

    def _join(self, user_id, store_id):
        self._check_personnel(store_id, user_id)
        self._lock_user(user_id)
        store = self.env['ydental.access.store'].sudo().browse(store_id).exists()
        user = self.env['res.users'].sudo().browse(user_id).exists()
        if not store or not store.active or not user or not user.active or not user._is_internal():
            raise AccessError(self.env._('access_denied: An active internal account and store are required.'))
        if not user.has_group('ydental_base.ydental_base_group_user'):
            # One-time application enrollment only. Store switches never alter
            # global groups or the account's default company.
            user.write({'group_ids': [fields.Command.link(self.env.ref('ydental_base.ydental_base_group_user').id)]})
        # Only the group can expand company access, never a store manager's arbitrary company command.
        if store.company_id not in user.company_ids:
            if not self._is_group_manager():
                raise AccessError(self.env._('access_denied: Company assignment requires group administration.'))
            user.write({'company_ids': [fields.Command.link(store.company_id.id)]})
        Employee = self.env['hr.employee'].sudo().with_context(active_test=False, no_reset_password=True)
        employee = Employee.search([('user_id', '=', user_id), ('company_id', '=', store.company_id.id)], limit=1)
        if not employee:
            employee = Employee.with_company(store.company_id).create({
                'name': user.name, 'user_id': user_id, 'company_id': store.company_id.id,
            })
        elif not employee.active:
            employee.write({'active': True})
        member = self._membership(user_id, store_id, active=False)
        if member and member.active:
            return member.id
        if member:
            member.write({'active': True, 'ydental_employee_id': employee.id})
        else:
            member = self.env['ydental.access.membership'].sudo().create({
                'ydental_user_id': user_id, 'ydental_store_id': store_id,
                'ydental_employee_id': employee.id,
            })
        self._audit('employment.join', 'personnel', member, store_id, after={'active': True})
        return member.id

    def _remove(self, user_id, store_id):
        self._check_personnel(store_id, user_id)
        self._lock_user(user_id)
        member = self._membership(user_id, store_id)
        if not member:
            return {'result': 'already_accepted'}
        if member.ydental_is_manager:
            raise UserError(self.env._('Manager appointment policy must be confirmed before removing a manager.'))
        self._grant(user_id, store_id, dict.fromkeys(dict(CATEGORIES), 'none'), source='employment.remove')
        member.write({'active': False})
        remaining = self.env['ydental.access.membership'].sudo().search([
            ('ydental_user_id', '=', user_id), ('active', '=', True),
            ('ydental_store_id.company_id', '=', member.ydental_store_id.company_id.id),
        ])
        if not remaining:
            member.ydental_employee_id.write({'active': False})
        self._after_membership_removed(member)
        self._audit('employment.remove', 'personnel', member, store_id, before={'active': True}, after={'active': False})
        return {'result': 'accepted'}

    def _after_membership_removed(self, membership):
        """S03 cancels/replans future assignments, with its own audited events."""
        return None

    def _depart(self, user_id):
        if not self._is_group_manager() or user_id == self.env.uid:
            raise AccessError(self.env._('access_denied: Group administration is required.'))
        self._scope(write=True)
        self._lock_user(user_id)
        user = self.env['res.users'].sudo().browse(user_id).exists()
        if not user or not user._is_internal():
            raise AccessError(self.env._('access_denied: An internal target account is required.'))
        self._check_user_company_scope(user)
        if not user.active:
            return {'result': 'already_accepted'}
        # The configurable replacement policy covers independent administrators
        # too. Serialize departures of different users before counting survivors.
        policy = self.env['ir.config_parameter'].sudo().get_str('ydental_access.manager_policy')
        if policy == 'group_with_replacement':
            self._lock_user(0)
            for group_xmlid in (GROUP_MANAGER, SYSTEM_MANAGER):
                if user.has_group(group_xmlid) and not self.env['res.users'].sudo().search_count([
                    ('id', '!=', user_id), ('active', '=', True),
                    ('all_group_ids', 'in', self.env.ref(group_xmlid).ids),
                ]):
                    raise UserError(self.env._('Assign a replacement before removing the last active administrator.'))
        members = self.env['ydental.access.membership'].sudo().search([('ydental_user_id', '=', user_id)])
        if any(members.mapped('ydental_is_manager')):
            raise UserError(self.env._('Manager appointment policy must be confirmed before removing a manager.'))
        for member in members:
            self._remove(user_id, member.ydental_store_id.id)
        employees = self.env['hr.employee'].sudo().search([('user_id', '=', user_id)])
        employees.write({'active': False})
        user.write({'active': False})
        self._audit('employment.depart', 'personnel', user, after={'active': False})
        return {'result': 'accepted'}

    def _audit_rows(self):
        session = self._scope()
        domain = fields.Domain.AND([
            fields.Domain('ydental_user_id', '=', self.env.uid),
            fields.Domain('ydental_category', '=', 'personnel'),
        ])
        own = self._membership(self.env.uid, session.ydental_store_id.id)
        if self._is_group_manager():
            domain |= fields.Domain.AND([
                fields.Domain('ydental_category', '=', 'personnel'),
                fields.Domain.OR([
                    fields.Domain('ydental_store_id', '=', False),
                    fields.Domain('ydental_store_id.company_id', 'in', self.env.user.company_ids.ids),
                ]),
            ])
        if own and (own.ydental_is_manager or self._levels(own)['personnel'] in ('read', 'write')):
            domain |= fields.Domain.AND([
                fields.Domain('ydental_store_id', '=', session.ydental_store_id.id),
                fields.Domain('ydental_category', '=', 'personnel'),
            ])
        if own:
            categories = [key for key, value in self._levels(own).items() if value != 'none']
            domain |= fields.Domain.AND([
                fields.Domain('ydental_store_id', '=', session.ydental_store_id.id),
                fields.Domain('ydental_category', 'in', categories),
            ])
        # Query events describe a model-level operation (target ID 0), and
        # are visible only to their actor in the same current store.
        domain |= fields.Domain.AND([
            fields.Domain('ydental_category', '=', 'query'),
            fields.Domain('ydental_user_id', '=', self.env.uid),
            fields.Domain('ydental_store_id', '=', session.ydental_store_id.id),
        ])
        # Check the actual source even for clinical event metadata. Never use
        # an audit record as a route around source-record reading permission.
        rows = self.env['ydental.access.audit'].sudo().search(domain, limit=100)
        visible = rows.browse()
        sources = self._get_sources().values()
        for row in rows:
            if row.ydental_category == 'personnel':
                if self._is_group_manager():
                    if row.ydental_store_id:
                        if row.ydental_store_id.company_id not in self.env.user.company_ids:
                            continue
                    else:
                        target = (self.env['res.users'].sudo().with_context(active_test=False).browse(
                            row.ydental_target_id).exists() if row.ydental_target_model == 'res.users'
                            else row.ydental_user_id)
                        if not target or not self._user_company_ids(target) <= set(self.env.user.company_ids.ids):
                            continue
                    targets = (row.ydental_after or {}).get('targets', [])
                    if targets:
                        stores = self.env['ydental.access.store'].sudo().with_context(active_test=False).browse(
                            [target[1] for target in targets]).exists()
                        if not set(stores.company_id.ids) <= set(self.env.user.company_ids.ids):
                            continue
                    visible |= row
                elif not row.ydental_store_id or row.ydental_store_id == session.ydental_store_id:
                    visible |= row
            elif row.ydental_target_model in sources:
                if row.ydental_category == 'query' and (
                    row.ydental_user_id.id != self.env.uid or
                    row.ydental_store_id != session.ydental_store_id or row.ydental_target_id != 0
                ):
                    continue
                source = self.env[row.ydental_target_model].browse(
                    [] if row.ydental_category == 'query' else row.ydental_target_id)
                try:
                    source.check_access('read')
                except AccessError:
                    continue
                visible |= row
        return visible.read(['ydental_event', 'ydental_result', 'ydental_target_model',
                             'ydental_target_id', 'ydental_before', 'ydental_after', 'create_date'])
