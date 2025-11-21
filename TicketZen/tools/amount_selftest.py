from addons.ocr import postprocess_fr

SAMPLES = {
    "9,42": 9.42,
    "942": 9.42,
    "12.34": 12.34,
    "1 234,56": 1234.56,
}


if __name__ == "__main__":
    for sample, expected in SAMPLES.items():
        parsed = postprocess_fr._parse_amount_fr(sample)
        status = "OK" if abs((parsed or 0) - expected) < 0.001 else "KO"
        print(f"{status}: {sample} -> {parsed}")
