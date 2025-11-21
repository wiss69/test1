import re
from pathlib import Path
from typing import Optional

import yaml
from rapidfuzz import fuzz

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "merchants.yml"


def load_merchants():
    if DATA_FILE.exists():
        return yaml.safe_load(DATA_FILE.read_text()) or {}
    return {"merchants": []}


DATA = load_merchants()


def resolve_merchant(candidate: Optional[str]) -> Optional[str]:
    if not candidate:
        return None
    merchants = DATA.get("merchants", [])
    normalized = candidate.strip().lower()
    best_match = None
    best_score = 0
    for merchant in merchants:
        canonical = merchant.get("name")
        aliases = merchant.get("aliases", [])
        regexes = merchant.get("regex", [])
        for pattern in regexes:
            if re.search(pattern, candidate, re.IGNORECASE):
                return canonical
        for alias in aliases + [canonical]:
            score = fuzz.token_sort_ratio(normalized, alias.lower())
            if score > best_score:
                best_score = score
                best_match = canonical
    if best_score > 60:
        return best_match
    return candidate


def default_category(merchant: Optional[str]) -> Optional[str]:
    if not merchant:
        return None
    for merch in DATA.get("merchants", []):
        if merch.get("name") == merchant:
            return merch.get("default_category")
    return None
