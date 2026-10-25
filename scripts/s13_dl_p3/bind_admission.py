#!/usr/bin/env python3
"""Bind fresh observed facts after a named independent reviewer receipt.

This writes only S13 private metadata. It does not declare business acceptance,
start services, connect to any database or silently renew an old admission.
"""
import argparse
import datetime as dt
import json
from pathlib import Path

from admission_probe import BRANCH, CORE, OID, PLAN, PRIVATE, ROOT, TARGET, git, write_receipt
from protected_snapshot import file_digest, private_json
import launcher


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe',type=Path,required=True)
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--review',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=PRIVATE/'admission.json')
    args=parser.parse_args();args.output=args.output.resolve()
    runtime=private_json(PRIVATE/'runtime.json');probe=private_json(args.probe.resolve())
    checkpoint=private_json(args.checkpoint.resolve());review=private_json(args.review.resolve())
    now=dt.datetime.now(dt.UTC);observed=dt.datetime.fromisoformat(probe['finished_at_utc'])
    if not dt.timedelta() <= now-observed <= dt.timedelta(minutes=30):
        raise RuntimeError('A fresh observed target probe is required.')
    if probe.get('status')!='READONLY_TARGET_IDENTITY_AND_GRANTS_OBSERVED' or not probe.get('rollback_idle') or not probe.get('connection_closed'):
        raise RuntimeError('Probe is incomplete or did not close its read-only connection.')
    candidate=runtime['candidate_commit']
    if candidate!=git('rev-parse','HEAD') or probe.get('candidate_commit')!=candidate or git('branch','--show-current')!=BRANCH:
        raise RuntimeError('Actual candidate, runtime and probe must match.')
    if checkpoint.get('status') not in ('READONLY_PROTECTED_UPGRADE_SNAPSHOT_COMPLETE','READONLY_PROTECTED_BASELINE_COMPLETE_NO_UPGRADE_AUTHORIZATION') or checkpoint.get('database')!=TARGET or checkpoint.get('database_oid')!=OID:
        raise RuntimeError('A complete checkpoint for this sole target is required.')
    reviewer=review.get('reviewer')
    if not isinstance(reviewer,str) or reviewer in ('/root','/root/tester') or not reviewer.strip():
        raise RuntimeError('The actual independent verifier must identify itself.')
    required={'status':'DLP3_RUNTIME_ADMISSION_REVIEWED','candidate_commit':candidate,
              'probe_sha256':file_digest(args.probe),'checkpoint_sha256':file_digest(args.checkpoint),
              'runtime_sha256':file_digest(PRIVATE/'runtime.json'),'launcher_sha256':file_digest(Path(launcher.__file__))}
    if any(review.get(key)!=value for key,value in required.items()):
        raise RuntimeError('Independent review does not bind these exact observed artifacts.')
    if review.get('reviewed_no_product_or_test_tool_implementation') is not True:
        raise RuntimeError('The review must state the real non-implementer boundary.')
    _env,proof=launcher.runtime_child_environment(runtime)
    identity=probe['identity'];db=runtime['database'];scope=runtime['scope'];application=runtime['application']
    value={'plan_id':PLAN,'branch':BRANCH,'candidate_commit':candidate,'core_commit':CORE,
           'database_name':TARGET,'database_oid':OID,'cluster_ref':identity['cluster_ref'],
           'database_user':db['user'],'database_host':db['host'],'database_port':db['port'],'database_server_addr':identity['server_addr'],
           'http_host':application['host'],'http_port':application['port'],'dbfilter':application['dbfilter'],
           'scope_id':scope['id'],'scope_plan_id':PLAN,'scope_expires_at_utc':scope['expires_at_utc'],
           'runtime_config_sha256':file_digest(PRIVATE/'runtime.json'),'external_message_provider_enabled':False,'outbound_smtp_servers':0,
           'target_identity_verified':True,'database_grants_verified':True,'database_role_not_superuser':True,
           'module_install_upgrade_permission_verified':True,'target_protection_checkpoint_verified':True,
           'target_protection_checkpoint_sha256':file_digest(args.checkpoint),'verified_by':reviewer,'verified_at_utc':now.isoformat(),
           'verification_receipt':str(args.review.resolve().relative_to(ROOT)),'verification_receipt_sha256':file_digest(args.review),
           'allowed_company_ids':probe['company_ids'],'allowed_store_ids':[row['id'] for row in probe['stores']],
           'installed_modules':[row['name'] for row in probe['modules']],
           'launcher_sha256':file_digest(Path(launcher.__file__)),'base_launcher_sha256':file_digest(ROOT/'scripts/s11/launcher.py'),
           'pdf_environment_adapter_sha256':file_digest(ROOT/'scripts/s12/launcher.py'),'runtime_environment_proof':proof,
           'probe_path':str(args.probe.resolve().relative_to(ROOT)),'probe_sha256':file_digest(args.probe),
           'shared_os_not_isolation':True,'purpose':'DL-P3 saved originals list/status/trace/pagination only; no P4-P6, new originals, economic actions or production'}
    digest=write_receipt(args.output,value)
    print(json.dumps({'status':'DLP3_OBSERVED_FACTS_BOUND_AFTER_INDEPENDENT_REVIEW','output':str(args.output.relative_to(ROOT)),'sha256':digest,'reviewer':reviewer}))


if __name__=='__main__':
    main()
