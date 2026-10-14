"""Non-executable design for a future, separately authorized synthetic L2 fixture.

No Odoo import, database connection, subprocess, or file mutation is present.
This file documents the intended order and guard contract only.
"""

FUTURE_AUTH_COMMENT_ID = None
TARGET_DATABASE = None
TARGET_OID = None
TARGET_MARKER_SHA256 = None
FIXTURE_KEY = None
SOURCE_OID = 2100080

REQUIRED_GUARDS = (
    'new unique synthetic S10 name and OID, never a historical OID',
    'fixed PostgreSQL cluster, Odoo20 core, config SHA256 and marker SHA256',
    'source_oid=2100080; loopback-only egress, SMTP blocked and cron disabled',
    'unmodified ydental_settlement_test.pre_init_hook accepts the real new marker',
    'one-use attempt ledger before ORM writes; recheck inside owned cursor',
    'one self-owned transaction and at most one commit after every postcondition',
)

ORDERED_STEPS = (
    'S01: one existing company; one synthetic store; manager/frontdesk/doctor, HR and memberships; grants and sessions',
    'S06: explicitly set synthetic queue heartbeat=2 and timeout=600 via ir.config_parameter.set_str',
    'S06: call original queue._settings and assert (2, 600) before first report',
    'S07: exactly one warehouse setup before any controlled S05 pricelist; validate native group side effects',
    'S01/S05: one active capability and one care catalog through the formal service',
    'S03: one floor, reporting care area with positive missed limit, station, demo supply policy, business day and published slot',
    'S05: one store mapping, reviewed and published 100-unit synthetic price via formal service',
    'S07: one material product and lot; real receipt of 2 using inventory service',
    'S05/S06: one synthetic patient; reserve, arrive, report, enter, call and start using real service APIs',
    'S08: open and save document; execute one actual treatment with one material unit',
)

POSTCONDITIONS = (
    'one confirmed treatment event, one fee, exact S05 price snapshot and one consumption',
    'one lot, receipt 2, issue 1, two done native stock.move rows and remaining quant 1',
    'account.move, account.payment and account.partial.reconcile each zero',
    'settlement source/payment/refund/close, mail.mail each zero',
    '92 modules unchanged; historical OIDs and source filestore SHA256 unchanged',
    'every new filestore file SHA256 and attachment source explained; unknown orphan means STOP',
)


def run(*_args, **_kwargs):
    """No execution permission exists in D1.7-R2-0."""
    raise PermissionError('This draft cannot run. A new GPT authorization is required.')


if __name__ == '__main__':
    run()
