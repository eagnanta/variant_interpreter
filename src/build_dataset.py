import pandas as pd

# Load only the columns we need
COLS = [
    "GeneSymbol", "Name", "ClinicalSignificance",
    "PhenotypeList", "ReviewStatus", "Type",
    "Chromosome", "Start", "ReferenceAllele", "AlternateAllele"
]

print("Loading ClinVar data...")
df = pd.read_csv(
    "data/variant_summary.txt.gz",
    sep="\t",
    compression="gzip",
    usecols=COLS,
    low_memory=False
)

# Keep only human, single-gene, well-reviewed variants
df = df[df["ReviewStatus"].str.contains("criteria provided", na=False)]

# Select our target genes
TARGET_GENES = ["BRCA1", "TP53", "EGFR", "KRAS", "PTEN"]
df_filtered = df[df["GeneSymbol"].isin(TARGET_GENES)]

# Balance the dataset — sample across significance categories
categories = ["Pathogenic", "Benign", "Uncertain significance"]
samples = []

for cat in categories:
    subset = df_filtered[
        df_filtered["ClinicalSignificance"].str.contains(cat, na=False)
    ]
    # Take up to 10 per gene per category
    for gene in TARGET_GENES:
        gene_subset = subset[subset["GeneSymbol"] == gene].head(10)
        samples.append(gene_subset)

final_df = pd.concat(samples).drop_duplicates()

print(f"\nDataset shape: {final_df.shape}")
print("\nDistribution:")
print(final_df["GeneSymbol"].value_counts())
print("\nSignificance breakdown:")
print(final_df["ClinicalSignificance"].value_counts())

# Save
final_df.to_csv("data/variants_clean.csv", index=False)
print("\nSaved to data/variants_clean.csv ✓")
