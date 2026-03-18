import streamlit as st
import pandas as pd
import os
from groq import Groq

st.set_page_config(
    page_title="Variant Interpreter",
    page_icon="🧬",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #1c2333; }

    html, body, [class*="css"] {
        font-size: 18px !important;
    }
    h1 {
        font-size: 2.8rem !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        padding: 10px 0 5px 0 !important;
        border: none !important;
        background: none !important;
        border-bottom: 3px solid #4db8b8 !important;
    }
    h2, h3 {
        font-size: 1.6rem !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    p, li, span, div, .stMarkdown p {
        font-size: 1.2rem !important;
        color: #ffffff !important;
        line-height: 2.0 !important;
    }
    [data-testid="stMetricLabel"] p {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #a0b0b0 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        color: #4db8b8 !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #151c2c !important;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        font-size: 1.1rem !important;
        color: #ffffff !important;
    }
    hr { border-color: #2e3a4e !important; }

    .evidence-card {
        background-color: #243044;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 14px;
        border-left: 4px solid #4db8b8;
    }
    .evidence-card h4 {
        color: #4db8b8;
        font-size: 1rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
        font-weight: 600;
    }
    .evidence-card p {
        color: #ffffff !important;
        font-size: 1.3rem !important;
        font-weight: 600;
        margin: 0;
    }

    .interpretation-box {
        background-color: #1a2e2e;
        border-radius: 10px;
        padding: 24px 28px;
        border: 1px solid #4db8b8;
        margin-bottom: 16px;
    }
    .interpretation-box * {
        color: #ffffff !important;
        font-size: 1.2rem !important;
        line-height: 2.1 !important;
    }

    .score-row {
        display: flex;
        gap: 12px;
        margin-top: 10px;
    }
    .score-card {
        flex: 1;
        background-color: #243044;
        border-radius: 10px;
        padding: 16px;
        border-top: 3px solid #4db8b8;
        text-align: center;
    }
    .score-card .label {
        color: #8aa0b8 !important;
        font-size: 0.95rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .score-card .value {
        color: #4db8b8 !important;
        font-size: 1.4rem !important;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🧬 LLM-Assisted Variant Interpreter")
st.markdown("**Clinical interpretation of genomic variants** · ClinVar · Ensembl VEP · COSMIC · LLaMA 3.3")
st.divider()

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("data/interpretations_final.csv")

df = load_data()

# Sidebar
st.sidebar.header("Select Variant")
genes = ["All"] + sorted(df["GeneSymbol"].unique().tolist())
selected_gene = st.sidebar.selectbox("Filter by gene", genes)

if selected_gene != "All":
    filtered_df = df[df["GeneSymbol"] == selected_gene]
else:
    filtered_df = df

selected_variant = st.sidebar.selectbox(
    "Select variant",
    filtered_df["Name"].tolist()
)

st.sidebar.divider()
st.sidebar.header("Interpret a new variant")
custom_gene = st.sidebar.text_input("Gene symbol (e.g. TP53)")
custom_variant = st.sidebar.text_input("Variant name (e.g. p.R175H)")
run_custom = st.sidebar.button("Interpret new variant")

# Get selected variant data
variant_data = filtered_df[filtered_df["Name"] == selected_variant].iloc[0]

# Main panel
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Variant Evidence")

    st.markdown(f"""
    <div class="evidence-card">
        <h4>Gene</h4>
        <p>{variant_data['GeneSymbol']}</p>
    </div>
    <div class="evidence-card">
        <h4>Variant</h4>
        <p style="font-size:1rem !important">{variant_data['Name']}</p>
    </div>
    """, unsafe_allow_html=True)

    sig = variant_data['significance_clean']
    if "Pathogenic" in sig and "Likely" not in sig:
        st.error(f"🔴 **Clinical Significance:** {sig}")
    elif "Likely pathogenic" in sig:
        st.error(f"🟠 **Clinical Significance:** {sig}")
    elif "Benign" in sig and "Likely" not in sig:
        st.success(f"🟢 **Clinical Significance:** {sig}")
    elif "Likely benign" in sig:
        st.success(f"🟡 **Clinical Significance:** {sig}")
    else:
        st.warning(f"⚪ **Clinical Significance:** {sig}")

    st.divider()
    st.markdown("**Functional Annotation**")

    consequence = variant_data['consequence'] if pd.notna(variant_data['consequence']) else "N/A"
    impact = variant_data['impact'] if pd.notna(variant_data['impact']) else "N/A"
    sift = round(variant_data['sift_score'], 3) if pd.notna(variant_data['sift_score']) else "N/A"
    polyphen = round(variant_data['polyphen_score'], 3) if pd.notna(variant_data['polyphen_score']) else "N/A"

    st.markdown(f"""
    <div class="score-row">
        <div class="score-card">
            <div class="label">Consequence</div>
            <div class="value" style="font-size:1rem !important">{consequence}</div>
        </div>
        <div class="score-card">
            <div class="label">Impact</div>
            <div class="value">{impact}</div>
        </div>
        <div class="score-card">
            <div class="label">SIFT</div>
            <div class="value">{sift}</div>
        </div>
        <div class="score-card">
            <div class="label">PolyPhen</div>
            <div class="value">{polyphen}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("**COSMIC Evidence**")
    if variant_data['cosmic_match']:
        st.success(f"✅ Found in **{int(variant_data['cosmic_count'])}** tumor samples")
    else:
        st.info("No COSMIC match found")

with col2:
    st.subheader("LLM Clinical Interpretation")

    if pd.notna(variant_data['llm_interpretation']):
        st.markdown(f"""
        <div class="interpretation-box">
            {variant_data['llm_interpretation'].replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No interpretation available for this variant")

    result_df = pd.DataFrame([{
        "Gene": variant_data['GeneSymbol'],
        "Variant": variant_data['Name'],
        "Clinical Significance": variant_data['significance_clean'],
        "Consequence": variant_data['consequence'],
        "Impact": variant_data['impact'],
        "SIFT": variant_data['sift_score'],
        "PolyPhen": variant_data['polyphen_score'],
        "COSMIC match": variant_data['cosmic_match'],
        "COSMIC count": variant_data['cosmic_count'],
        "LLM Interpretation": variant_data['llm_interpretation']
    }])

    csv = result_df.to_csv(index=False)
    st.download_button(
        label="⬇️ Download this interpretation as CSV",
        data=csv,
        file_name=f"{variant_data['GeneSymbol']}_{variant_data['Name'][:20]}.csv",
        mime="text/csv"
    )

# Custom variant interpretation
if run_custom and custom_gene and custom_variant:
    st.divider()
    st.subheader(f"New interpretation: {custom_gene} — {custom_variant}")

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    prompt = f"""You are a clinical genomics assistant. Based ONLY on the evidence provided below,
write a concise clinical interpretation of this variant.

Your interpretation must cover exactly these four points:
1. Classification: What is the ClinVar clinical significance of this variant?
2. Functional impact: Based on the SIFT score, is the amino acid change deleterious or tolerated?
3. Protein damage: Based on the PolyPhen score, is the variant probably damaging, possibly damaging, or benign?
4. Cancer evidence: Has this variant been observed in tumor samples in COSMIC?

Write in clear clinical language. Do not add information beyond what is provided.
If a score is not available, state that clearly but use other available evidence to reason about the variant's likely effect.

VARIANT DATA:
Gene: {custom_gene}
Variant: {custom_variant}
Clinical Significance: Not yet classified
SIFT score: not available
PolyPhen score: not available
COSMIC evidence: not available"""

    with st.spinner("Generating interpretation..."):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        st.markdown(f"""
        <div class="interpretation-box">
            {response.choices[0].message.content.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

# Footer
st.divider()
st.caption("Built with ClinVar · Ensembl VEP · COSMIC · Groq LLaMA 3.3 · Streamlit")
