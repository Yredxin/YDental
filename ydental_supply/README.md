# Isolated synthetic supply target

The historical isolated-test target remains available under its existing exact
identity checks. A separate, explicitly authorised isolated environment may
configure one additional target for its Odoo process. Set
`YDENTAL_E2E_ISOLATED_SUPPLY=1` and supply `YDENTAL_E2E_ISOLATED_TARGET` as a
JSON object with exactly these fields: `database` (ASCII letters, digits and
underscores), `oid` (positive PostgreSQL database OID integer), `cluster`
(decimal PostgreSQL system identifier string), and `store_id` (positive Odoo
store ID integer). The configuration must contain the actual database and
store identity, not an alias or wildcard. Missing, malformed, extra, duplicate
or mismatched fields deny this additional target. Do not commit actual target
configuration; supply it from a private local provider to the test process.

This configuration is an administrative test-scope control, not proof of
isolation. Independently verify database identity, contents, network and
external channels before use. It does not authorize formal publication; the
existing isolated-test approval, business permissions and validation still
apply. Remove the configuration and stop the test process after use.
