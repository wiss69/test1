import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from rapidfuzz import fuzz

from addons.knowledge import merchants as merch_knowledge
from addons.knowledge import header_name
from addons.classify import categories

LOGGER = logging.getLogger("ticketzen.postprocess")


def dump_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _parse_amount_fr(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    txt = text.strip().replace(" ", "")
    txt = txt.replace("€", "")
    txt = txt.replace("'", "")
    match = re.search(r"([0-9]+[\.,][0-9]{2})", txt)
    if not match:
        if txt.isdigit():
            return float(int(txt) / 100)
        return None
    candidate = match.group(1).replace(",", ".")
    try:
        return float(candidate)
    except ValueError:
        return None


def _parse_date(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"]:
        try:
            return datetime.strptime(text.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _extract_header(meta_lines: List[Dict[str, Any]], heuristics: Dict[str, Any]) -> Optional[str]:
    if not meta_lines:
        return None
    top_n = int(heuristics.get("TZ_HEADER_TOP_N", 20))
    candidates = sorted(meta_lines, key=lambda l: l.get("y_norm", 0))[:top_n]
    filtered = [l for l in candidates if not header_name.looks_like_address(l.get("text", ""))]
    if filtered:
        return filtered[0].get("text")
    return candidates[0].get("text") if candidates else None


def normalize_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    heuristics = {
        "TZ_HEADER_TOP_N": int(_env_or_default("TZ_HEADER_TOP_N", 20)),
        "TZ_HEADER_MIN_SCORE": int(_env_or_default("TZ_HEADER_MIN_SCORE", 42)),
        "TZ_MERCHANT_MIN_SCORE": int(_env_or_default("TZ_MERCHANT_MIN_SCORE", 88)),
    }
    fields = raw.get("fields", {})
    merchant_name = fields.get("merchant")
    header_candidate = _extract_header(raw.get("meta", {}).get("lines", []), heuristics)
    merchant = merch_knowledge.resolve_merchant(merchant_name or header_candidate)
    total = _parse_amount_fr(fields.get("total") or raw.get("texts"))
    date_achat = _parse_date(fields.get("date_achat"))
    lignes = fields.get("lignes") or []
    category = categories.categorize(merchant)
    return {
        "merchant": merchant,
        "date": date_achat,
        "total": total,
        "lignes": lignes,
        "category": category,
        "conf": raw.get("conf"),
        "tags": raw.get("warnings", []),
        "header": header_candidate,
        "texts": raw.get("texts", ""),
    }


def _env_or_default(key: str, default: int) -> int:
    import os

    try:
        return int(os.getenv(key, default))
    except ValueError:
        return default
