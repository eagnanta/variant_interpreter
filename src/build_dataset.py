import pandas as pd

COLS = [
    "GeneSymbol", "Name", "ClinicalSignificance",
    "PhenotypeList", "ReviewStatus", "Type",
    "Chromosome", "Start", "ReferenceAlleleVCF", "AlternateAlleleVCF"
]

print("Loading ClinVar data...")
df = pd.read_csv(
    "data/variant_summary.txt.gz",
    sep="\t",
    compression="gzip",
    usecols=COLS,
    low_memory=False
)

df = df[df["ReviewStatus"].str.contains("criteria provided", na=False)]

TARGET_GENES = ["BRCA1", "TP53", "EGFR", "KRAS", "PTEN", "APC", "MLH1", "MSH2", "STK11", "PALB2"]

categories = ["Pathogenic", "Benign", "Uncertain significance"]
samples = []

for cat in categories:
    subset = df[
        (df["ClinicalSignificance"].str.contains(cat, case=False, na=False)) &
        (df["GeneSymbol"].isin(TARGET_GENES))
    ]
    for gene in TARGET_GENES:
        gene_subset = subset[subset["GeneSymbol"] == gene].head(40)
        samples.append(gene_subset)

final_df = pd.concat(samples).drop_duplicates()

final_df = final_df[
    (final_df["ReferenceAlleleVCF"].notna()) & (final_df["ReferenceAlleleVCF"] != "na") &
    (final_df["AlternateAlleleVCF"].notna()) & (final_df["AlternateAlleleVCF"] != "na")
]

final_df = final_df.rename(columns={
    "Chromosome": "chr",
    "Start": "pos",
    "ReferenceAlleleVCF": "ref",
    "AlternateAlleleVCF": "alt"
})

def assign_priority(row):
    sig = str(row['ClinicalSignificance']).lower()
    if 'pathogenic' in sig: return 'HIGH_RISK'
    if 'benign' in sig: return 'LOW_RISK'
    return 'VUS'

final_df['priority_flag'] = final_df.apply(assign_priority, axis=1)

# Save
final_df.to_csv("data/variants_clean.csv", index=False)

print("-" * 30)
print(f"SUCCESS: Created dataset with {len(final_df)} variants.")
print(f"Columns: {list(final_df.columns)}")
print("-" * 30)
