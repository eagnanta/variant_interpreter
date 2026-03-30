import pandas as pd
import os
import time
from groq import Groq

# 1. Setup Client and Data
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment!")

client = Groq(api_key=api_key)
data_path = "data/interpretations_final.csv"

if not os.path.exists(data_path):
    print(f"Error: {data_path} not found. Running the main pipeline first?")
    exit(1)

df = pd.read_csv(data_path)

# 2. Define the Prompt Builder (Matches your main pipeline logic)
def build_prompt(row):
    return f"""
    Provide a clinical interpretation for the following genetic variant:
    - Gene: {row.get('GeneSymbol', 'N/A')}
    - Variant: {row.get('Name', 'N/A')}
    - ClinVar Significance: {row.get('significance_clean', 'N/A')}
    - SIFT Score: {row.get('sift_score', 'N/A')}
    - PolyPhen Score: {row.get('polyphen_score', 'N/A')}
    - COSMIC Count: {row.get('cosmic_count', 0)}
    - Tumor Types: {row.get('tumor_types', 'Unknown')}

    Please format the response in exactly these four points:
    1. Classification: Summarize ClinVar status.
    2. Functional impact: Interpret SIFT/PolyPhen (if N/A, use variant type like {row.get('consequence', 'unknown')}).
    3. Protein damage: Assess structural damage.
    4. Cancer evidence: Mention the COSMIC count and the specific tumor types listed above.
    """

# 3. Filter for broken rows
# This targets anything containing "ERROR" or "Rate limit"
to_fix = df[df['llm_interpretation'].str.contains("ERROR|limit", na=True, case=False)].copy()

if to_fix.empty:
    print("✨ No errors found! All variants have valid interpretations.")
    exit(0)

print(f"🚀 Found {len(to_fix)} variants to repair. Starting recovery...")

# 4. Processing Loop
for i, row in to_fix.iterrows():
    print(f"[{i}] Repairing: {row['GeneSymbol']} - {row['Name'][:40]}...")
    
    try:
        prompt = build_prompt(row)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Lighter model to avoid 429 errors
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        interpretation = response.choices[0].message.content
        df.at[i, 'llm_interpretation'] = interpretation
        
        # Save every row to prevent losing progress if it crashes
        df.to_csv(data_path, index=False)
        
        # Brief pause to respect Rate Limits (Requests Per Minute)
        time.sleep(1.5) 
        
    except Exception as e:
        print(f"❌ Failed again at index {i}: {str(e)}")
        continue

print(f"\n✅ Repair process finished. Final results saved to {data_path}")
