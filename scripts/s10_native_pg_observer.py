"""Bounded, read-only PostgreSQL activity observer self-test for S10 D1.3.

This tool never starts Odoo and only selects its own synthetic application tag.
"""

import argparse
import configparser
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import threading
import time

import psycopg2
from psycopg2.extensions import TRANSACTION_STATUS_IDLE


ROOT = Path(__file__).resolve().parents[2]
CLUSTER = "7694897083368259627"
APP_PATTERN = re.compile(r"s10_d13_selftest_[a-f0-9]{12}\Z")
QUERY = (
    "SELECT pid, state, backend_start, state_change "
    "FROM pg_stat_activity WHERE datname = %s AND application_name = %s"
)


def endpoint():
    parser = configparser.ConfigParser(interpolation=None)
    if not parser.read(ROOT / "odoo.conf"):
        raise RuntimeError("locked config missing")
    options = parser["options"]
    if (options["db_host"], options["db_port"], options["db_user"]) != (
        "127.0.0.1", "5432", "odoo"
    ):
        raise RuntimeError("PostgreSQL endpoint mismatch")
    return {
        "host": "127.0.0.1",
        "port": 5432,
        "user": "odoo",
        "password": options["db_password"],
        "connect_timeout": 5,
        "dbname": "postgres",
        "options": "-c statement_timeout=5000 -c default_transaction_read_only=on",
    }


def assert_fresh(conn):
    if not conn.autocommit or conn.get_transaction_status() != TRANSACTION_STATUS_IDLE:
        raise RuntimeError("observer requires autocommit and idle transaction")


def sample(conn, application_name):
    if not APP_PATTERN.fullmatch(application_name):
        raise RuntimeError("invalid synthetic application tag")
    assert_fresh(conn)
    with conn.cursor() as cursor:
        cursor.execute(QUERY, ("postgres", application_name))
        rows = cursor.fetchall()
    assert_fresh(conn)
    if len(rows) > 1:
        raise RuntimeError("synthetic tag collision")
    return [
        {
            "pid": pid,
            "state": state,
            "backend_start": start.isoformat() if start else None,
            "state_change": changed.isoformat() if changed else None,
        }
        for pid, state, start, changed in rows
    ]


def selftest(application_name, output):
    if not APP_PATTERN.fullmatch(application_name):
        raise RuntimeError("invalid synthetic application tag")
    if output.exists() or output.is_symlink() or output.parent.stat().st_mode & 0o077:
        raise RuntimeError("private output path must be new in a 700 directory")
    ready = threading.Event()
    subject = {}

    def sleeper():
        try:
            conn = psycopg2.connect(**endpoint(), application_name=application_name)
            try:
                conn.set_session(readonly=True, autocommit=True)
                with conn.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    subject["pid"] = cursor.fetchone()[0]
                    ready.set()
                    cursor.execute("SELECT pg_sleep(3)")
                    cursor.fetchone()
            finally:
                conn.close()
        except BaseException as error:
            subject["error"] = type(error).__name__ + ": " + str(error)
            ready.set()

    observer = psycopg2.connect(**endpoint(), application_name="s10_d13_observer")
    try:
        observer.set_session(readonly=True, autocommit=True)
        assert_fresh(observer)
        with observer.cursor() as cursor:
            cursor.execute("SELECT current_database(), system_identifier::text FROM pg_control_system()")
            identity = cursor.fetchone()
        if identity != ("postgres", CLUSTER):
            raise RuntimeError("management database or cluster mismatch")
        before = sample(observer, application_name)
        if before:
            raise RuntimeError("synthetic application tag already in use")
        thread = threading.Thread(target=sleeper, daemon=True)
        thread.start()
        if not ready.wait(5):
            raise RuntimeError("synthetic subject did not start")
        if "error" in subject:
            raise RuntimeError("synthetic subject failed: " + subject["error"])
        seen = []
        for _ in range(6):
            seen.append({"utc": datetime.now(timezone.utc).isoformat(), "rows": sample(observer, application_name)})
            if any(row["pid"] == subject["pid"] and row["state"] == "active" for row in seen[-1]["rows"]):
                break
            time.sleep(0.25)
        thread.join(timeout=5)
        if thread.is_alive() or "error" in subject:
            raise RuntimeError("synthetic subject failed to complete")
        after = sample(observer, application_name)
        result = {
            "management_database": "postgres",
            "cluster": CLUSTER,
            "subject_backend_pid": subject["pid"],
            "observer_backend_pid": observer.get_backend_pid(),
            "before": before,
            "samples": seen,
            "after": after,
            "observed_active": any(
                row["pid"] == subject["pid"] and row["state"] == "active"
                for entry in seen for row in entry["rows"]
            ),
            "session_count": 2,
            "odoo_process_count": 0,
        }
        with os.fdopen(os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "w") as file:
            json.dump(result, file, ensure_ascii=False, indent=2)
            file.write("\n")
        if before or after or not result["observed_active"]:
            raise RuntimeError("observer did not see fresh synthetic activity")
        return result
    finally:
        observer.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true", required=True)
    parser.add_argument("--application-name", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(selftest(args.application_name, args.output)))
