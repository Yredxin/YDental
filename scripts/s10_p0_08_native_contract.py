"""Read fixed installed native login + inheritance without creating an Odoo registry."""
from copy import deepcopy
from functools import lru_cache
import json
from lxml import etree
import s10_p0_08_control as c


@lru_cache(maxsize=1)
def login_fixture():
    source=c.load_capture(c.PRIVATE/'source-initial-readonly.json')['managed']
    base=source['views']['web.login']['arch']['en_US']
    node=etree.fromstring(base.encode())
    form=node.xpath('.//form')[0]
    form.set('action','/web/login')
    # list_db=False makes db_list unavailable; debug is not requested.
    for el in list(form.xpath('.//*[@t-if]')):
        if el.get('t-if') in ('databases and len(databases) > 1','debug','error','message'):
            el.getparent().remove(el)
    inherited=etree.fromstring(source['views']['auth_passkey.auth_passkey_login']['arch']['en_US'].encode())
    xp=inherited.find('xpath')
    assert xp.get('expr')=="//input[@name='redirect']" and xp.get('position')=='before'
    redirect=form.xpath('.//input[@name="redirect"]')[0]
    for el in xp:redirect.addprevious(deepcopy(el))
    vals={'csrf_token':'SIMULATED_CSRF','login':'SYNTHETIC','password':'SYNTHETIC',
        'type':'password','webauthn_response':'','redirect':'/ydental/access'}
    for el in form.xpath('.//input[@name]'):el.set('value',vals[el.get('name')])
    form.set('class','oe_login_form')
    form.attrib.pop('onsubmit',None) # native action has no fragment in this contract
    return etree.tostring(form,encoding='unicode',method='html')


def main():
    source=c.load_capture(c.PRIVATE/'source-initial-readonly.json')['managed']
    paths=['addons/web/controllers/home.py','addons/web/controllers/utils.py',
        'addons/web/views/webclient_templates.xml','addons/auth_signup/controllers/main.py',
        'addons/auth_passkey/controllers/main.py','addons/auth_passkey/views/auth_passkey_login_templates.xml',
        'addons/auth_passkey/static/src/interactions/passkey_login.js']
    assert all((c.CORE/p).is_file() for p in paths)
    native={p:c.s.file_sha(c.CORE/p) for p in paths}
    local=['ydental_access/controllers/access.py','ydental_access/views/ydental_access_templates.xml',
           'ydental_access/models/ydental_access_service.py','scripts/s10_p0_06_browser.py','scripts/s10_p0_07_browser.py']
    native.update({p:c.s.file_sha(c.ROOT/p) for p in local})
    keys=['web.login','web.login_layout','web.login_oauth','auth_signup.login','auth_passkey.auth_passkey_login']
    views={k:{'id':source['views'][k]['row']['id'],'inherit_id':source['views'][k]['row']['inherit_id'],
        'languages':{lang:c.s.sha(arch.encode()) for lang,arch in source['views'][k]['arch'].items()}}
        for k in keys}
    assert source['modules']['auth_passkey']['state']=='installed'
    assets=[]
    for row in c.load_capture(c.PRIVATE/'source-initial-readonly.json')['all']['rows']['ir_attachment'].values():
        if (row['url'] or '').startswith('/web/assets/'):
            f=c.s.SOURCE_RUN/'data/filestore'/c.s.SOURCE/row['store_fname']
            assets.append({k:row[k] for k in ('id','url','file_size','checksum','mimetype','store_fname')}|{'sha256':c.s.file_sha(f)})
    from s10_p0_08_browser import ASSETS,LOGIN_FIELDS
    assert {a['url'] for a in assets}==ASSETS
    data={'status':'STATIC_INSTALLED_NATIVE_CONTRACT_PASS','source_files':native,'installed_views':views,
        'login':{'method':'POST','path':'/web/login','fields':sorted(LOGIN_FIELDS),'each_count':1,
            'webauthn_response':'empty_only','type':'password_only','redirect':'/ydental/access',
            'query':[],'content_type':'application/x-www-form-urlencoded','db_control':'absent_list_db_false',
            'csrf':'DOM_token_hash_exact','actor':'SQL_login_hash_exact','password':'existing_P006_synthetic_only'},
        'switch':{'fields':['csrf_token','operation','revision','store_id'],'revision':0,'stores':{'6':1,'14':3}},
        'existing_assets':assets,'new_assets':0,'new_files':0,'old_files':'all_exact',
        'resource_limits':{'assets_per_path_actor':6,'translations_actor':6,'access_actor':2,'login_actor':1,'all_GETs':90},
        'P007_failure_cause':'UNKNOWN_NOT_CAPTURED','proven_contract_difference':'installed_auth_passkey_adds_webauthn_response',
        'fixture_sha256':c.s.sha(login_fixture().encode())}
    c.save_once(c.PRIVATE/'native-contract.json',data)
    print(json.dumps({'status':data['status'],'fields':data['login']['fields'],'assets':len(assets)}))


if __name__=='__main__':main()
