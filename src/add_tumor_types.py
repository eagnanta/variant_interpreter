import pandas as pd

# Load classification file
print("Loading COSMIC classification file...")
classification = pd.read_csv(
    "data/Cosmic_Classification_v103_GRCh37.tsv",
    sep="\t",
    usecols=["COSMIC_PHENOTYPE_ID", "PRIMARY_SITE", "PRIMARY_HISTOLOGY"]
)

print(f"Classification entries: {len(classification)}")
print(classification.head(3).to_string())

# Load our variants
df = pd.read_csv("data/variants_cosmic.csv")

def map_tumor_types(phenotype_ids):
    """Map COSMIC phenotype IDs to tumor type names."""
    if pd.isna(phenotype_ids):
        return None
    
    ids = str(phenotype_ids).split(";")
    tumor_types = []
    
    for pid in ids:
        pid = pid.strip()
        match = classification[classification["COSMIC_PHENOTYPE_ID"] == pid]
        if len(match) > 0:
            site = match["PRIMARY_SITE"].iloc[0]
            histology = match["PRIMARY_HISTOLOGY"].iloc[0]
            if site != "NS" and histology != "NS":
                tumor_types.append(f"{site} {histology}")
            elif site != "NS":
                tumor_types.append(site)
    
    # Remove duplicates and return
    unique_types = list(dict.fromkeys(tumor_types))
    return "; ".join(unique_types[:3]) if unique_types else None

print("\nMapping tumor types...")
df["tumor_types"] = df["cosmic_phenotypes"].apply(map_tumor_types)

# Check results
matched = df[df["tumor_types"].notna()]
print(f"\nVariants with tumor type names: {len(matched)}")
print("\nSample mappings:")
print(matched[["GeneSymbol", "cosmic_count", "tumor_types"]].head(10).to_string())

df.to_csv("data/variants_cosmic.csv", index=False)
print("\nSaved to data/variants_cosmic.csv ✓")
