"""Unapproved D1.5 L1 fixture draft. Never execute under the current grant.

The future authorization sentinel is deliberately unset. This module performs
no work on import, and its command-line entry always refuses execution.
"""

import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat


FUTURE_AUTH_COMMENT_ID = None
CORE_SHA = "f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb"
PG_CLUSTER = "7694897083368259627"
PURE_92_TEMPLATE_OID = 2100080
HISTORICAL_OIDS = {2056451, 2078375, 2100078, 2100079, 2100080}
PRIVATE_ROOT = Path('/home/redxin/code/odoo/odoo-sd/code/sd-addons/.local')


def validate_guard(env, run_dir):
    """Check a future new database before any write; this batch always fails."""
    if FUTURE_AUTH_COMMENT_ID is None:
        raise PermissionError("Future GPT authorization has not been granted")
    run = Path(run_dir)
    database = env.cr.dbname
    if (not re.fullmatch(r"ydental_s10_test_[0-9]{14}_[a-f0-9]{8}", database)
            or run.name != database or run.is_symlink() or not run.is_dir()
            or run.parent.resolve() != PRIVATE_ROOT.resolve()
            or stat.S_IMODE(run.stat().st_mode) != 0o700
            or os.environ.get("YDENTAL_S10_RUN_DIR") != str(run)):
        raise PermissionError("Synthetic run identity mismatch")
    config_path, marker_path = run / "odoo.conf", run / "database.json"
    policy_path = run / "network-policy" / "sitecustomize.py"
    data_dir = run / "data"
    filestore = data_dir / "filestore" / database
    if (not config_path.is_file() or config_path.is_symlink()
            or not marker_path.is_file() or marker_path.is_symlink()
            or not policy_path.is_file() or policy_path.is_symlink()
            or not data_dir.is_dir() or data_dir.is_symlink()
            or not filestore.is_dir() or filestore.is_symlink()
            or stat.S_IMODE(config_path.stat().st_mode) != 0o600
            or stat.S_IMODE(marker_path.stat().st_mode) != 0o600):
        raise PermissionError("Private config or marker missing")
    marker = json.loads(marker_path.read_text())
    config_sha = hashlib.sha256(config_path.read_bytes()).hexdigest()
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(config_path):
        raise PermissionError("Config unreadable")
    options = config["options"]
    env.cr.execute("SELECT oid FROM pg_database WHERE datname=%s", [database])
    row = env.cr.fetchone()
    env.cr.execute("SELECT system_identifier::text FROM pg_control_system()")
    cluster_row = env.cr.fetchone()
    if (not row or not cluster_row or row[0] in HISTORICAL_OIDS
            or marker.get("oid") != row[0] or marker.get("database") != database
            or marker.get("cluster") != cluster_row[0] or cluster_row[0] != PG_CLUSTER
            or marker.get("core") != CORE_SHA or marker.get("core_sha") != CORE_SHA
            or marker.get("config_sha256") != config_sha
            or marker.get("network_policy_sha256") != hashlib.sha256(policy_path.read_bytes()).hexdigest()
            or os.environ.get("PYTHONPATH", "").split(os.pathsep)[0] != str(policy_path.parent)
            or not re.fullmatch(r"[a-f0-9]{16}", str(marker.get("fixture_key", "")))
            or marker.get("source_oid") != PURE_92_TEMPLATE_OID
            or marker.get("future_authorization_comment_id") != FUTURE_AUTH_COMMENT_ID
            or marker.get("egress") != "loopback_only"
            or options.get("db_host") != "127.0.0.1" or options.get("db_port") != "5432"
            or options.get("db_name") != database or options.get("dbfilter") != "^" + database + "$"
            or options.get("data_dir") != str(run / "data")
            or options.get("http_interface") != "127.0.0.1"
            or options.get("http_port") != str(marker.get("port"))
            or not 18000 <= int(marker.get("port", 0)) <= 18999
            or options.get("list_db", "").lower() != "false"
            or options.get("workers") != "0"
            or options.get("smtp_server") != "127.0.0.1" or options.get("smtp_port") != "1"
            or options.get("max_cron_threads") != "0"):
        raise PermissionError("Native fixture guard rejected database or network identity")
    env.cr.execute("SELECT state FROM ir_module_module WHERE name='ydental_settlement_test'")
    installed = env.cr.fetchone()
    if not installed or installed[0] != "installed":
        raise PermissionError("92-module state required")
    return marker


def prepare_l1(shell_env, run_dir):
    """Future-only synthetic access fixture; one owned cursor and one commit."""
    marker = validate_guard(shell_env, run_dir)
    from odoo import api
    from odoo.tests import new_test_user

    with shell_env.registry.cursor() as cursor:
        env = api.Environment(cursor, 1, {})
        root = env["base"].sudo().env
        fixture_name = "D1.5 Synthetic L1 " + marker["fixture_key"]
        if root["ydental.access.store"].search_count([("name", "=", fixture_name)]):
            raise PermissionError("Fixture already exists; stop and inspect the first commit")
        store = root["ydental.access.store"].create({
            "name": fixture_name,
            "company_id": root.company.id,
            "ydental_timezone": "UTC",
        })
        manager = new_test_user(
            root,
            name="D1.5 Synthetic Manager",
            login="d15_" + marker["fixture_key"],
            password=secrets.token_urlsafe(24),
            groups="ydental_base.ydental_base_group_user,ydental_access.ydental_group_manager",
        )
        access = root["ydental.access.service"].with_user(manager)
        session = access._session_for_key("d15-l1-" + marker["fixture_key"])
        admin = access._bind(session)
        admin._join(manager.id, store.id)
        admin._grant(manager.id, store.id, {"frontdesk": "write", "medical": "write"})
        if marker["oid"] in HISTORICAL_OIDS:
            raise PermissionError("Historical database cannot receive a fixture")
        cursor.commit()


if __name__ == "__main__":
    raise SystemExit("NOT_AUTHORIZED: D1.5-0 permits offline design only")
