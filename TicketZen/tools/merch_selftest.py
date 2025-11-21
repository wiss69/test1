from addons.knowledge import merchants

SAMPLES = ["E LECLERC", "gamm vert", "Big M", "carrefour city"]

if __name__ == "__main__":
    for sample in SAMPLES:
        print(f"{sample} => {merchants.resolve_merchant(sample)} (cat={merchants.default_category(merchants.resolve_merchant(sample))})")
