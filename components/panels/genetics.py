import streamlit as st

ss = st.session_state

from components.handlers import (
    _get_gene_data,
)


def genetics_panel():
    gene, patient = st.tabs(["Gene view", "Patient view"])

    with gene:
        gene_panel()

    with patient:
        st.text_input("Enter patient ID:", key="patient_id")


def gene_panel():
    gene_name = st.text_input("Enter gene name (case-insensitive):")

    # if input, show table
    if gene_name:
        # get data
        cn_df, vn_df = _get_gene_data(gene_name.upper())

        cnas = 0
        vnas = 0

        cna_text = "CNAs"
        if cn_df is not None:
            cnas = cn_df.shape[0]
            if cnas == 1:
                cna_text = "CNA"

        vna_text = "variants"
        if vn_df is not None:
            vnas = vn_df.shape[0]
            if vnas == 1:
                vna_text = "variant"

        # genomespy link
        st.markdown(
            f"{cnas} {cna_text}, {vnas} {vna_text}. Links: "
            f"[GenomeSpy](https://genomespy.app/decider/gene/{gene_name}) "
        )

        if cn_df is None and vn_df is None:
            st.write("No data found for this gene.")

        if cn_df is not None:
            st.markdown("#### Copy Number Alterations")
            st.dataframe(cn_df, hide_index=False)

        if vn_df is not None:
            st.markdown("#### Sequence Variants")
            st.dataframe(vn_df, hide_index=False)
