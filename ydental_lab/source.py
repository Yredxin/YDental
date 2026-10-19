from dataclasses import dataclass


@dataclass(frozen=True)
class LabStockSource:
    actor_id: int
    store_id: int
    order_id: int
    operation: str
