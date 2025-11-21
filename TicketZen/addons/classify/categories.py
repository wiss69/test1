from addons.knowledge import merchants

GENERIC_DEFAULT = "divers"


def categorize(merchant_name):
    default = merchants.default_category(merchant_name)
    if default:
        return default
    if merchant_name:
        lower = merchant_name.lower()
        if any(term in lower for term in ["fnac", "darty"]):
            return "électronique"
        if any(term in lower for term in ["restaurant", "café", "bistro"]):
            return "restauration"
    return GENERIC_DEFAULT
