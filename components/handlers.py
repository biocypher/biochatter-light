# HANDLERS
import datetime
import streamlit as st

ss = st.session_state
import os

import streamlit.components.v1 as components
from biochatter._stats import get_community_usage_cost
from streamlit.runtime.uploaded_file_manager import (
    UploadedFile,
    UploadedFileRec,
)
from streamlit.proto.Common_pb2 import FileURLs
import pandas as pd
from .kg import _connect_to_neo4j


def update_api_keys():
    """
    Looks for API keys of supported services in the environment variables and
    updates the session state accordingly.
    """
    if "OPENAI_API_KEY" in os.environ:
        ss.openai_api_key = os.environ["OPENAI_API_KEY"]
    if "HUGGINGFACEHUB_API_TOKEN" in os.environ:
        ss.huggingfacehub_api_key = os.environ["HUGGINGFACEHUB_API_TOKEN"]

    if "OPENAI_API_TYPE" in os.environ:
        if os.environ["OPENAI_API_TYPE"] == "azure":
            set_azure_mode()


def set_azure_mode():
    if not "OPENAI_DEPLOYMENT_NAME" in os.environ:
        raise ValueError(
            "OPENAI_DEPLOYMENT_NAME must be set to use Azure API. Please use it to "
            "set the deployment name, e.g. OPENAI_DEPLOYMENT_NAME=your-deployment-name"
        )

    if not "OPENAI_MODEL_NAME" in os.environ:
        raise ValueError(
            "OPENAI_MODEL_NAME must be set to use Azure API. Please use it to set "
            "the model name, e.g. OPENAI_MODEL_NAME=gpt-35-turbo"
        )

    if not "OPENAI_API_VERSION" in os.environ:
        raise ValueError(
            "OPENAI_API_VERSION must be set to use Azure API. Please use it to "
            "set the API version, e.g. OPENAI_API_VERSION=2023-03-15-preview"
        )

    if not "OPENAI_API_BASE" in os.environ:
        raise ValueError(
            "OPENAI_API_BASE must be set to use Azure API. Please use it to "
            "set the API base, e.g. "
            "OPENAI_API_BASE=https://your-resource-name.openai.azure.com"
        )

    if not "OPENAI_API_KEY" in os.environ:
        raise ValueError(
            "OPENAI_API_KEY must be set to use Azure API, e.g. "
            "OPENAI_API_KEY=sk-1234567890abcdef1234567890abcdef"
        )

    ss.openai_api_type = "azure"
    ss.openai_deployment_name = os.environ["OPENAI_DEPLOYMENT_NAME"]
    ss.openai_api_version = os.environ["OPENAI_API_VERSION"]
    ss.openai_api_base = os.environ["OPENAI_API_BASE"]
    ss.openai_api_key = os.environ["OPENAI_API_KEY"]
    # check for key validity?
    ss.mode = "getting_name"


def on_submit():
    """
    Handles the submission of the input text.
    """
    ss.input = ss.get("widget")
    ss.widget = ""


def autofocus_line():
    """
    Autofocuses the input line. A bit hacky, but works.
    """
    if "counter" not in ss:
        ss["counter"] = 0
    components.html(
        f"""
        <div></div>
        <p>{ss.counter}</p>
        <script>
            var input = window.parent.document.querySelectorAll("input[type=text]");
            for (var i = 0; i < input.length; ++i) {{
                input[i].focus();
            }}
        </script>
        """,
        height=15,
    )


def autofocus_area():
    """
    Autofocuses the input area. A bit hacky, but works.
    """
    if "counter" not in ss:
        ss["counter"] = 0
    components.html(
        f"""
        <div></div>
        <p>{ss.counter}</p>
        <script>
            var input = window.parent.document.querySelectorAll("textarea[type=textarea]");
            for (var i = 0; i < input.length; ++i) {{
                input[i].focus();
            }}
        </script>
        """,
        height=15,
    )


def _change_model():
    """
    Handles the user changing the primary model.
    """
    if ss.primary_model == ss._primary_model:
        return

    ss.primary_model = ss._primary_model
    ss.mode = ""
    ss.input = ""


def use_community_key():
    """
    Use the community key for the conversation.
    """
    ss.openai_api_key = os.environ["OPENAI_COMMUNITY_KEY"]
    ss.bcl._history_only("📎 Assistant", "Using community key!")
    ss.user = "community"
    ss.mode = "using_community_key"
    ss.show_community_select = False
    ss.input = "done"  # just to enter main logic; more elegant solution?


def get_remaining_tokens():
    """
    Fetch the percentage of remaining tokens for the day from the _stats module.
    """
    used = get_community_usage_cost()
    limit = float(99 / 30)
    pct = (100.0 * (limit - used) / limit) if limit else 0
    pct = max(0, pct)
    pct = min(100, pct)
    return pct


def community_tokens_refresh_in():
    """
    Display the time remaining until the community tokens refresh.
    """
    x = datetime.datetime.now()
    dt = (x.replace(hour=23, minute=59, second=59) - x).seconds
    h = dt // 3600
    m = dt % 3600 // 60
    return f"{h} h {m} min"


def demo_next():
    """
    Handle demo mode logic.
    """
    if ss.mode == "demo_key":
        ss.input = "Demo User"
        ss.mode = "demo_start"

    elif ss.mode == "demo_start":
        ss.input = (
            "Immunity; single-cell sequencing of PBMCs of a healthy donor, "
            "3000 cells; followed by pathway activity analysis."
        )
        ss.mode = "demo_context"

    elif ss.mode == "demo_context":
        # create UploadedFile from "input/progeny.csv"
        with open("input/progeny.csv", "rb") as f:
            data = f.read()

        uploaded_file = UploadedFileRec(
            file_id=1,
            name="progeny.csv",
            type="text/csv",
            data=data,
        )

        ss.demo_tool_data = [
            UploadedFile(record=uploaded_file, file_urls=FileURLs())
        ]
        ss.mode = "demo_tool"
        ss.input = "done"

    elif ss.mode == "demo_tool":
        ss.input = "no"
        ss.mode = "demo_manual"

    elif ss.mode == "demo_manual":
        ss.input = "Please explain my findings."
        ss.mode = "demo_chat"


def reset_app():
    """
    Reset the app to its initial state.
    """
    ss.clear()
    ss._primary_model = "gpt-3.5-turbo"


def data_input_yes():
    """
    Handles the user clicking the "Yes" button for uploading a file containing
    their tool data.
    """
    ss.mode = "getting_data_file_input"
    ss.input = "done"


def data_input_no():
    """
    Handles the user clicking the "No" button for uploading a file containing
    their tool data.
    """
    ss.mode = "asking_for_manual_data_input"
    ss.input = "no"


def demo_mode():
    """
    Enter the demo mode for the conversation.
    """
    ss.openai_api_key = os.environ["OPENAI_COMMUNITY_KEY"]
    ss.bcl._history_only("📎 Assistant", "Using community key!")
    ss.user = "community"
    ss.show_community_select = False
    ss.input = "Demo User"
    ss.mode = "demo_key"


def shuffle_messages(l: list, i: int):
    """Replaces the message at position i with the message at position 3, and
    moves the replaced message to the end of the list."""
    l[i], l[3] = (
        l[3],
        l[i],
    )
    l.append(l.pop(3))


def set_data_mode():
    ss.conversation_mode = "data"
    ss.bcl._ask_for_context("data")


def set_papers_mode():
    ss.conversation_mode = "papers"
    ss.bcl._ask_for_context("papers")


def set_both_mode():
    ss.conversation_mode = "both"
    ss.bcl._ask_for_context("data and papers")


def refresh():
    ss.input = ""
    st.rerun()


def _rerun_query():
    """
    Rerun the query using the modified query.
    """
    ss.generate_query = False


def _regenerate_query():
    """
    Regenerate the query using the new question.
    """
    ss.generate_query = True


def _get_gene_data(gene_name):
    """
    Get gene data from the API.
    """
    _connect_to_neo4j()

    gene_id = "hgnc:" + gene_name

    result = ss.neodriver.query(
        "MATCH (g:Gene) "
        "WHERE g.id = $gene_id "
        "OPTIONAL MATCH (g)<-[cn:SampleToGeneCopyNumberAlteration]-(cns:Sample)"
        "OPTIONAL MATCH (g)<-[vn:VariantToGeneAssociation]-(v:SequenceVariant)<-[ss:SampleToVariantAssociation]-(vns:Sample)"
        "RETURN g, cns, v, vns, "
        "cn.id, cn.breaksInGene, cn.nMajor, cn.nMinor, cn.purifiedBaf, cn.purifiedLogR, cn.minPurifiedLogR, cn.maxPurifiedLogR, cn.purifiedLoh, "
        "vn.id, "
        "ss.id ",
        gene_id=gene_id,
    )

    if not result[0]:
        return None, None

    patterns = result[0]
    # header: gene information (should be the same gene in all rows)
    gene = patterns[0]["g"]
    read_name = str(gene["id"]).replace("hgnc:", "")
    st.markdown(
        f"""
                ### Gene: {read_name} ({gene['ID']})
                chr: {gene['chr']}, start: {gene['start']}, end: {gene['end']}
                """
    )
    # format result as dataframe
    # for each pattern, create row(s) in dataframe
    cn_df = pd.DataFrame(
        columns=[
            "alteration_id",
            "breaks_in_gene",
            "n_major",
            "n_minor",
            "purified_baf",
            "purified_logr",
            "min_purified_logr",
            "max_purified_logr",
            "purified_loh",
            "sample_id",
        ]
    )
    vn_df = pd.DataFrame(
        columns=[
            "alteration_id",
            "mane",
            "cadd_phred",
            "aa_mane",
            "func_mane",
            "ex_func_mane",
            "clnsig",
            "clnrevstat",
            "gnomad_max",
            "ref",
            "alt",
            "pos",
            "cosmic_total_occ",
            "sample_id",
        ]
    )
    for pattern in patterns:
        # get copy numbers
        if pattern.get("cn.id") is not None:
            if pattern["cn.id"] in cn_df["alteration_id"]:
                pass
            else:
                cn_id = pattern["cn.id"]
                cn_breaks = pattern["cn.breaksInGene"]
                cn_n_major = pattern["cn.nMajor"]
                cn_n_minor = pattern["cn.nMinor"]
                cn_purified_baf = pattern["cn.purifiedBaf"]
                cn_purified_logr = pattern["cn.purifiedLogR"]
                cn_min_purified_logr = pattern["cn.minPurifiedLogR"]
                cn_max_purified_logr = pattern["cn.maxPurifiedLogR"]
                cn_purified_loh = pattern["cn.purifiedLoh"]
                cns = pattern["cns"]["id"]
                cn_df = cn_df.append(
                    {
                        "alteration_id": cn_id,
                        "breaks_in_gene": cn_breaks,
                        "n_major": cn_n_major,
                        "n_minor": cn_n_minor,
                        "purified_baf": cn_purified_baf,
                        "purified_logr": cn_purified_logr,
                        "min_purified_logr": cn_min_purified_logr,
                        "max_purified_logr": cn_max_purified_logr,
                        "purified_loh": cn_purified_loh,
                        "sample_id": cns,
                    },
                    ignore_index=True,
                )
        # get variants
        if pattern.get("vn.id") is not None:
            if pattern["vn.id"] in list(vn_df["alteration_id"]):
                pass
            else:
                vn_id = pattern["vn.id"]
                v_mane = pattern["v"]["Gene.MANE"]
                v_cadd = pattern["v"]["CADD_phred"]
                aa_mane = pattern["v"]["AAChange.MANE"]
                func_mane = pattern["v"]["Func.MANE"]
                ex_func_mane = pattern["v"]["ExonicFunc.MANE"]
                v_clnsig = pattern["v"]["CLNSIG"]
                v_clnrevstat = pattern["v"]["CLNREVSTAT"]
                v_gnomad_max = pattern["v"]["gnomAD_genome_max"]
                v_ref = pattern["v"]["REF"]
                v_alt = pattern["v"]["ALT"]
                v_pos = pattern["v"]["POS"]
                v_totocc = pattern["v"]["COSMIC_TOTAL_OCC"]
                vns = pattern["vns"]["id"]
                vn_df = vn_df.append(
                    {
                        "alteration_id": vn_id,
                        "mane": v_mane,
                        "cadd_phred": v_cadd,
                        "aa_mane": aa_mane,
                        "func_mane": func_mane,
                        "ex_func_mane": ex_func_mane,
                        "clnsig": v_clnsig,
                        "clnrevstat": v_clnrevstat,
                        "gnomad_max": v_gnomad_max,
                        "ref": v_ref,
                        "alt": v_alt,
                        "pos": v_pos,
                        "cosmic_total_occ": v_totocc,
                        "sample_id": vns,
                    },
                    ignore_index=True,
                )

    # aggregate cn_df grouping samples in new column "sample_ids", drop
    # "sample_id" and duplicate rows
    cn_df["sample_ids"] = cn_df.groupby("alteration_id")["sample_id"].transform(
        lambda x: ",".join(x)
    )
    cn_df = cn_df.drop(columns=["sample_id"])
    cn_df = cn_df.drop_duplicates()

    return cn_df, vn_df


def toggle_rag_agent_prompt():
    """Toggles the use of the rag_agent prompt."""
    ss.use_rag_agent = not ss.use_rag_agent


def toggle_split_by_characters():
    """Toggles the splitting of the input text by characters vs tokens."""
    ss.rag_agent.split_by_characters = not ss.rag_agent.split_by_characters
