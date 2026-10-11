from dataclasses import dataclass


CATEGORIES = [
    ('frontdesk', 'Front desk'), ('patient', 'Patient'),
    ('medical', 'Medical'), ('exam', 'Examination'),
    ('pharmacy', 'Pharmacy'), ('warehouse', 'Warehouse'),
    ('followup', 'Follow-up contact'), ('outsourcing', 'Outsourcing'),
    ('settlement', 'Settlement'), ('finance_approval', 'Financial approval'),
    ('personnel', 'Personnel authorization'), ('space', 'Space'),
    ('capacity', 'Schedule and capacity'), ('price', 'Price'),
    ('supplier', 'Supplier cooperation'), ('export', 'Report export'),
]
LEVELS = [('none', 'None'), ('read', 'Read only'), ('write', 'Read and write')]
RANK = {'none': 0, 'read': 1, 'write': 2}
GROUP_MANAGER = 'ydental_access.ydental_group_manager'
SYSTEM_MANAGER = 'ydental_access.ydental_system_manager'


@dataclass(frozen=True)
class Binding:
    """Server-created request scope; JSON context cannot construct this object."""
    user_id: int
    session_id: int
    revision: int
