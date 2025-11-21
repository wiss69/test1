import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import requests

DEFAULT_WARNINGS = ["azure_route=documentintelligence", "azure_api=2024-07-31"]


def _request_azure(content: bytes, content_type: str, endpoint: str, api_path: str, key: str, timeout: int, logger: logging.Logger):
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": content_type,
    }
    url = f"{endpoint.rstrip('/')}/{api_path.lstrip('/')}"
    try:
        resp = requests.post(url, headers=headers, data=content, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Azure request failed for %s: %s", api_path, exc)
        return None


def _azure_paths(route: str, api_version: str) -> List[str]:
    if route == "documentintelligence":
        return [f"documentintelligence/documentModels/prebuilt-receipt:analyze?api-version=2024-07-31"]
    if route == "formrecognizer":
        return [f"formrecognizer/documentModels/prebuilt-receipt:analyze?api-version=2023-10-31"]
    return [
        "formrecognizer/v2.1/prebuilt/receipt/analyze?includeTextDetails=true",
    ]


def _normalize_v21(resp: Dict[str, Any]) -> Dict[str, Any]:
    result = {"fields": {}, "conf": None, "texts": "", "meta": {"lines": []}, "warnings": []}
    read_results = resp.get("analyzeResult", {}).get("readResults") or []
    lines = []
    texts = []
    for page in read_results:
        for line in page.get("lines", []):
            line_text = line.get("text", "")
            texts.append(line_text)
            if page.get("height"):
                y_norm = line.get("boundingBox", [0, 0, 0, 0])[1] / page.get("height")
            else:
                y_norm = 0
            lines.append({"text": line_text, "y_norm": y_norm, "page": page.get("page", 1)})
    result["texts"] = "\n".join(texts)
    result["meta"]["lines"] = lines
    document_results = resp.get("analyzeResult", {}).get("documentResults") or []
    if document_results:
        fields = document_results[0].get("fields", {})
        merchant = fields.get("MerchantName", {}).get("text")
        purchase_date = fields.get("TransactionDate", {}).get("text")
        total = None
        total_field = fields.get("Total") or fields.get("TotalDue")
        if total_field:
            total = total_field.get("text") or total_field.get("valueNumber")
        items = []
        for item in fields.get("Items", []):
            if isinstance(item, dict):
                name = item.get("valueObject", {}).get("Name", {}).get("text") or item.get("text")
                price = item.get("valueObject", {}).get("TotalPrice", {}).get("text")
                items.append({"name": name, "price": price})
        result["fields"] = {
            "merchant": merchant,
            "date_achat": purchase_date,
            "total": total,
            "lignes": items,
        }
    return result


def _normalize_azure(resp: Dict[str, Any]) -> Dict[str, Any]:
    documents = resp.get("documents") or resp.get("analyzeResult", {}).get("documents") or []
    texts = resp.get("content", "")
    lines_meta = []
    pages = resp.get("pages", [])
    for page in pages:
        page_num = page.get("pageNumber") or page.get("page") or 1
        height = page.get("height") or 1
        for line in page.get("lines", []):
            y_norm = (line.get("boundingPolygon", [{}])[0].get("y", 0) / height) if height else 0
            lines_meta.append({"text": line.get("content", ""), "y_norm": y_norm, "page": page_num})
    fields = {}
    if documents:
        doc = documents[0]
        field_map = doc.get("fields", {})
        def _text(field_name):
            field = field_map.get(field_name, {})
            return field.get("content") or field.get("valueString") or field.get("value")
        fields = {
            "merchant": _text("MerchantName") or _text("Merchant") or _text("VendorName"),
            "date_achat": _text("TransactionDate") or _text("PurchaseDate"),
            "total": _text("Total") or _text("TotalDue"),
            "lignes": [],
        }
        items = field_map.get("Items")
        if items and isinstance(items.get("valueArray", []), list):
            for item in items.get("valueArray", []):
                obj = item.get("valueObject", {})
                fields["lignes"].append({
                    "name": obj.get("Name", {}).get("content"),
                    "price": obj.get("TotalPrice", {}).get("content"),
                })
    return {"fields": fields, "conf": None, "texts": texts, "meta": {"lines": lines_meta}, "warnings": []}


def analyze_document(content: bytes, content_type: str, config: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    logger = logger or logging.getLogger("ticketzen.azure")
    if config.get("dry_run") or not config.get("cloud_enabled") or not config.get("endpoint") or not config.get("key"):
        logger.info("Azure in dry-run or disabled mode; returning stub result")
        return {
            "fields": {"merchant": "Netto", "date_achat": "2024-05-01", "total": "9,42", "lignes": [{"name": "Pain", "price": "1,00"}]},
            "conf": 0.8,
            "texts": "Netto\n01/05/2024\nTotal 9,42",
            "meta": {"lines": [{"text": "Netto", "y_norm": 0.05, "page": 1}]},
            "warnings": ["dry_run=true"],
        }

    routes = ["documentintelligence", "formrecognizer", "formrecognizer_v21"]
    ordered_routes = [config.get("route") or "documentintelligence"] + [r for r in routes if r != config.get("route")]
    api_versions = {
        "documentintelligence": "2024-07-31",
        "formrecognizer": "2023-10-31",
        "formrecognizer_v21": "v2.1",
    }

    for route in ordered_routes:
        paths = _azure_paths(route, config.get("api_version", api_versions.get(route, "v2.1")))
        for path in paths:
            response = _request_azure(content, content_type, config.get("endpoint", ""), path, config.get("key", ""), config.get("timeout", 90), logger)
            if response:
                if route == "formrecognizer_v21":
                    normalized = _normalize_v21(response)
                else:
                    normalized = _normalize_azure(response)
                normalized["warnings"].append(f"azure_route={route}")
                normalized["warnings"].append(f"azure_api={config.get('api_version', api_versions.get(route))}")
                _save_debug(normalized)
                return normalized
    fallback = {
        "fields": {"merchant": None, "date_achat": None, "total": None, "lignes": []},
        "conf": None,
        "texts": "",
        "meta": {"lines": []},
        "warnings": ["azure_all_failed"],
    }
    _save_debug(fallback)
    return fallback


def _save_debug(payload: Dict[str, Any]):
    try:
        Path("last_azure.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        if payload.get("meta"):
            Path("last_azure_meta.json").write_text(json.dumps(payload.get("meta"), ensure_ascii=False, indent=2))
    except Exception:  # pragma: no cover - defensive
        pass
