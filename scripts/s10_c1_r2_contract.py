"""Small, payload-free contracts for the bounded Odoo-C1-R2 fixture."""


def classify_sql(query):
    """Record only the expected application lock class, never SQL parameters."""
    sql = str(query).upper()
    if 'PG_ADVISORY_XACT_LOCK' in sql:
        return 'inventory_advisory_lock'
    if 'UPDATE YDENTAL_INVENTORY_MUTEX' in sql:
        return 'inventory_mutex_update'
    if 'LOCK TABLE STOCK_WAREHOUSE IN SHARE ROW EXCLUSIVE MODE' in sql:
        return 'warehouse_table_lock'
    if 'FROM RES_GROUPS WHERE ID = %S FOR UPDATE' in sql:
        return 'group_user_row_lock'
    return None


def lock_order(events):
    """Report the observed order of the two S07 product lock statements."""
    wanted = ('warehouse_table_lock', 'group_user_row_lock')
    ordered = [event for event in events if event in wanted]
    return ordered == list(wanted)


def commit_slot(existing, requested):
    """Permit exactly the two named synthetic business commits."""
    allowed = ('baseline', 'warehouse')
    if (tuple(existing) != allowed[:len(existing)] or len(existing) >= len(allowed)
            or requested != allowed[len(existing)]):
        raise ValueError('Odoo-C1-R2 commit budget or sequence violation')
    return len(existing) + 1
