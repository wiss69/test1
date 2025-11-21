from addons.classify import categories

SAMPLES = ["Fnac", "Darty", "Restaurant Chez Paul", "Netto"]

if __name__ == "__main__":
    for sample in SAMPLES:
        print(f"{sample} => {categories.categorize(sample)}")
