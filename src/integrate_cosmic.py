import pandas as pd
import re

# Three-letter to single-letter amino acid conversion
AA_MAP = {
    'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D',
    'CYS': 'C', 'GLN': 'Q', 'GLU': 'E', 'GLY': 'G',
    'HIS': 'H', 'ILE': 'I', 'LEU': 'L', 'LYS': 'K',
    'MET': 'M', 'PHE': 'F', 'PRO': 'P', 'SER': 'S',
    'THR': 'T', 'TRP': 'W', 'TYR': 'Y', 'VAL': 'V',
    'TER': '*', 'SEC': 'U', 'PYL': 'O'
}

def three_to_one(aa_str):
    """Convert three-letter amino acid notation to single-letter.
    e.g. 'CYS64GLY' -> 'C64G'
    """
    if not aa_str:
        return None
    result = aa_str
    for three, one in AA_MAP.items():
        result = result.replace(three, one)
    return result

# Load our annotated variants
df = pd.read_csv("data/variants_annotated.csv")

TARGET_GENES = ["BRCA1", "TP53", "EGFR", "KRAS", "PTEN"]
COSMIC_COLS = [
    "GENE_SYMBOL", "GENOMIC_MUTATION_ID", "MUTATION_AA",
    "MUTATION_DESCRIPTION", "PUBMED_PMID", "HGVSP",
    "MUTATION_SOMATIC_STATUS", "COSMIC_PHENOTYPE_ID"
]

def extract_protein_change(name):
    if pd.isna(name):
        return None
    match = re.search(r'\(p\.([^)]+)\)', str(name))
    if match:
        raw = match.group(1).upper()
        return three_to_one(raw)
    return None

def normalize_cosmic_aa(aa):
    """Normalize COSMIC protein change.
    e.g. 'p.Glu258Lys' -> 'GLU258LYS'
    """
    if pd.isna(aa):
        return None
    aa = str(aa).strip()
    aa = re.sub(r'^p\.', '', aa)
    return aa.upper()

# Extract protein changes from our dataset
print("Extracting protein changes from ClinVar names...")
df["protein_change"] = df["Name"].apply(extract_protein_change)
print(f"Variants with extractable protein change: {df['protein_change'].notna().sum()}")
print("\nSample protein changes:")
print(df[["GeneSymbol", "Name", "protein_change"]].dropna().head(5).to_string())

# Load COSMIC in chunks
print("\nLoading COSMIC data in chunks...")
chunks = []
for chunk in pd.read_csv(
    "data/Cosmic_MutantCensus_v103_GRCh37.tsv",
    sep="\t",
    usecols=COSMIC_COLS,
    low_memory=False,
    chunksize=100000
):
    filtered = chunk[chunk["GENE_SYMBOL"].isin(TARGET_GENES)]
    if len(filtered) > 0:
        chunks.append(filtered)

cosmic_df = pd.concat(chunks).drop_duplicates()
print(f"COSMIC entries for target genes: {len(cosmic_df)}")
print(cosmic_df["GENE_SYMBOL"].value_counts())

# Normalize COSMIC protein changes
cosmic_df["aa_norm"] = cosmic_df["MUTATION_AA"].apply(normalize_cosmic_aa)
cosmic_df["hgvsp_norm"] = cosmic_df["HGVSP"].apply(normalize_cosmic_aa)

print("\nSample COSMIC normalized entries:")
print(cosmic_df[["GENE_SYMBOL","MUTATION_AA","aa_norm"]].dropna().head(5).to_string())

# Match variants to COSMIC
print("\nMatching variants to COSMIC...")
results = []

for i, row in df.iterrows():
    gene = row["GeneSymbol"]
    protein_change = row["protein_change"]

    gene_cosmic = cosmic_df[cosmic_df["GENE_SYMBOL"] == gene]

    if protein_change and not pd.isna(protein_change):
        matches = gene_cosmic[
            (gene_cosmic["aa_norm"] == protein_change) |
            (gene_cosmic["hgvsp_norm"] == protein_change)
        ]
    else:
        matches = pd.DataFrame()

    if len(matches) > 0:
        results.append({
            "cosmic_match": True,
            "cosmic_count": len(matches),
            "cosmic_mutation_ids": ";".join(matches["GENOMIC_MUTATION_ID"].dropna().unique()[:5].astype(str)),
            "cosmic_phenotypes": ";".join(matches["COSMIC_PHENOTYPE_ID"].dropna().unique()[:5].astype(str)),
            "cosmic_somatic_status": matches["MUTATION_SOMATIC_STATUS"].mode()[0] if len(matches) > 0 else None,
            "pubmed_pmids": ";".join(matches["PUBMED_PMID"].dropna().unique()[:5].astype(str))
        })
    else:
        results.append({
            "cosmic_match": False,
            "cosmic_count": 0,
            "cosmic_mutation_ids": None,
            "cosmic_phenotypes": None,
            "cosmic_somatic_status": None,
            "pubmed_pmids": None
        })

results_df = pd.DataFrame(results)
df_final = pd.concat([df.reset_index(drop=True), results_df], axis=1)

print(f"\n--- COSMIC Integration Summary ---")
print(f"Variants with COSMIC match: {results_df['cosmic_match'].sum()}")
print(f"Variants without match: {(~results_df['cosmic_match']).sum()}")
print(f"\nMatches by gene:")
print(df_final[df_final["cosmic_match"]==True]["GeneSymbol"].value_counts())

df_final.to_csv("data/variants_cosmic.csv", index=False)
print("\nSaved to data/variants_cosmic.csv ✓")
