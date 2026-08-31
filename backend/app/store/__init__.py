"""On-disk JSON document store for the workspace layer.

One file per aggregate, written atomically (temp + os.replace), guarded by an
in-process lock. No database by design — see PRODUCT_ROADMAP.md.
"""
from app.store.json_store import JsonStore, StoreError

__all__ = ["JsonStore", "StoreError"]
