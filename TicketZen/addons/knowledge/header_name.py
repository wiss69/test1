import re

ADDRESS_HINTS = ["avenue", "av.", "rue", "boulevard", "bd", "impasse", "chemin", "route", "bp", "boite", "boîte"]


def looks_like_address(text: str) -> bool:
    lower = text.lower()
    return any(hint in lower for hint in ADDRESS_HINTS) or bool(re.search(r"\d{2}\s\d{3}", lower))
