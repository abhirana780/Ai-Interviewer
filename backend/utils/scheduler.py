import re

def normalize_slot(slot: str) -> str:
    s = (slot or "").strip()
    # Accept formats like "YYYY-MM-DD HH:MM"; trim extra spaces
    s = re.sub(r"\s+", " ", s)
    return s

def is_valid_slot(slot: str) -> bool:
    if not slot:
        return False
    # Simple check: YYYY-MM-DD HH:MM
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})$", slot)
    if not m:
        return False
    y, mo, d, h, mi = map(int, m.groups())
    if not (1 <= mo <= 12 and 1 <= d <= 31 and 0 <= h <= 23 and 0 <= mi <= 59):
        return False
    return True