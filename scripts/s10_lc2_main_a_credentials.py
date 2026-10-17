"""Fixed MAIN-A test credential preparation, consumed only by owned Odoo shell.

This is an authentication fixture, not a clinical editor operation. Secret values
are read only from the private provider; neither values nor hashes are emitted.
"""
import json
from pathlib import Path
import stat


def prepare_main_a_credentials(env):
    # Odoo shell executes stdin without the script's real __file__.
    root = Path.cwd()
    private = root / '.local/s10-lc2-main-a-20261018-02'
    from s10_lc2_task_profile import main_a_autonomy_profile
    from s10_lc2_evidence import save_once
    profile = main_a_autonomy_profile()
    profile.verify()
    assert private == profile.root
    env.cr.execute("SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(SELECT system_identifier::text FROM pg_control_system()),current_user")
    assert env.cr.fetchone() == (profile.database, 2144129, '7694897083368259627', 'odoo')
    plan = json.loads((private / 'authentication-plan.json').read_bytes())
    assert plan['resource_owned_synthetic_test'] is True
    assert plan['other_connections_before_preparation'] == 0
    ids = plan['user_ids']
    assert type(ids) is list and 1 <= len(ids) <= 2 and ids[0] == 7 and len(set(ids)) == len(ids)
    assert all(type(uid) is int and uid > 1 for uid in ids)
    provider_dir = private / 'credentials'
    assert not provider_dir.is_symlink() and stat.S_IMODE(provider_dir.stat().st_mode) == 0o700
    clinical = env['ydental.clinical.service']
    access = env['ydental.access.service']
    document = env['ydental.clinical.document'].browse(1).exists()
    assert document.state == 'confirmed' and document.ydental_version == 4
    assert document.ydental_author_id.id == document.ydental_responsible_id.id == 7
    assert not clinical._valid_editor(document), 'VALID_EDITOR_PRESENT'
    assert clinical._eligible_responsible(document, env['res.users'].browse(7)), 'CLINICAL_USER_INELIGIBLE'

    def identity(user):
        member = access._membership(user.id, 1)
        return {'id': user.id, 'active': user.active, 'company_id': user.company_id.id,
                'company_ids': sorted(user.company_ids.ids), 'group_ids': sorted(user.group_ids.ids),
                'capability_ids': sorted(user.ydental_capability_ids.ids),
                'employee_ids': sorted(user.employee_ids.ids),
                'membership_id': member.id, 'employee_id': member.ydental_employee_id.id,
                'employee_active': member.ydental_employee_id.active,
                'levels': access._levels(member)}

    users = env['res.users'].browse(ids).exists()
    assert len(users) == len(ids)
    before = {user.id: identity(user) for user in users}
    original_user = env['res.users'].browse(plan['original_user_id'])
    reader = before[original_user.id]
    assert reader['active'] and reader['employee_active']
    assert reader['levels']['settlement'] in ('read', 'write') and reader['levels']['export'] == 'write'
    for user in users:
        path = provider_dir / ('user-%d.json' % user.id)
        assert not path.is_symlink() and stat.S_IMODE(path.stat().st_mode) == 0o600
        provider = json.loads(path.read_bytes())
        assert set(provider) == {'user_id', 'login', 'password'} and provider['user_id'] == user.id
        assert provider['login'] == user.login and isinstance(provider['password'], str) and len(provider['password']) >= 32
        # Native ORM setter supplies hashing and standard session invalidation.
        user.write({'password': provider['password']})
        del provider
    assert before == {user.id: identity(user) for user in users}, 'BUSINESS_IDENTITY_CHANGED'
    # Odoo shell otherwise rolls back; this task explicitly authorizes this authentication fixture commit.
    env.cr.commit()
    save_once(private / 'authentication-preparation.json', {
        'task_message_id': profile.message_id, 'user_ids': ids,
        'original_user_id': original_user.id, 'standard_orm_password_write': True,
        'transaction_commit_returned': True, 'business_identity_equal': True,
        'clinical_eligible': True, 'prior_editor_valid': False,
        'identity_before_after': before, 'clinical_editor_operation': False,
        'secret_values_or_hashes_emitted': False,
    })
    print('MAIN_A_AUTHENTICATION_PREPARATION_COMMITTED')


prepare_main_a_credentials(env)
