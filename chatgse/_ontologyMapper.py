# ChatGSE user ontology mapper class
# manage the ontology mapping

from loguru import logger
import pandas as pd
import streamlit as st
import text2term
import string

ss = st.session_state


# ENVIRONMENT VARIABLES


class OntologyMapper:
    def __init__(self):
        if "terms" not in ss:
            ss.terms = ""
        if "coulumn_Names" not in ss:
            ss.coulumn_Names = [
                "celltypes",
                "cell",
                "cells",
                "Zelltypen",
                "Zelle",
                "Zellen",
            ]
        if "map" not in ss:
            ss.map = False
        if "term_list" not in ss:
            ss.term_list = []
        if "mapped_term_list" not in ss:
            ss.mapped_term_list = []

    @staticmethod
    def _render_msg(role: str, msg: str):
        return f"`{role}`: {msg}"

    def _write_and_history(self, role: str, msg: str):
        logger.info(f"Writing message from {role}: {msg}")
        st.markdown(self._render_msg(role, msg))
        # ss.history.append({role: msg})  --> TODO: Add History to ontology mapping

    def cache_ontologies(self):
        """
        Set the text2term ontology to use for the mapping.
        """
        # TODO: Expand the method to use more than one ontology --> May a list where you can select the ontologies you want to use
        # TODO: Implement an file import so that you can map terms in files

        logger.info("Caching the Cell Ontology")

        text2term.cache_ontology("http://purl.obolibrary.org/obo/cl.owl", "CL")

    def _get_mapping(self):
        logger.info("Getting Mapping from text2term.")
        # extracting the terms and put them into a list
        # use ; , and \n as split between words
        # TODO: possibility to get the words from a file

        # List of words that will be mapped
        celltypes = []

        if ss.get("ontology_tool_data"):
            # reading the csv files
            dataframes = []
            for f in ss.ontology_tool_data:
                df_csv = pd.read_csv(f)
                dataframes.append(df_csv)

            # Extract the possible filenames and drop the NAN values and the punctuation:

            for df in dataframes:
                for name in ss.coulumn_Names:
                    # check if coulumn name exists
                    if name in df.columns:
                        # drop nans
                        df = df.dropna(subset=name)

                        # getting celltypes, removing the punctuation and convert it to a list
                        celltypes = (
                            celltypes
                            + df[name]
                            .str.replace("[{}]".format(string.punctuation), "")
                            .tolist()
                        )

        # Load Terms from ChatBox
        terms = (
            ss.terms.replace(";", "\n")
            .replace(",", "\n")
            .replace("[{}]".format(string.punctuation), "")
            .split("\n")
        )

        # Adding terms from the Box to the celltypes of the file
        celltypes = celltypes + terms

        # caching the ontologie if not exists
        if not text2term.cache_exists("CL"):
            self.cache_ontologies()

        # map the terms
        # TODO: Optional possibility to save the mappings
        result = text2term.map_terms(
            celltypes,
            "CL",
            base_iris="http://purl.obolibrary.org/obo/CL",
            use_cache=True,
        )

        # self._write_and_history("💬🧬 text2term", "mapping results",)
        # st.markdown(
        # f"""
        # ```
        # {result.to_markdown()}
        # """

        # )
        # For design
        # st.markdown("\n")

        # return result

        build_term_lists(result)


def build_term_lists(result):
    # maybe it would be better to use dictionary
    ss.term_list = []
    ss.mapped_term_list = []
    for index, row in result.iterrows():
        term = result["Source Term"][index]
        if term in ss.term_list:
            term_index = ss.term_list.index(term)
            ss.mapped_term_list[term_index].append(
                (row["Mapped Term Label"], row["Mapping Score"])
            )
        else:
            ss.term_list.append(term)
            mapped_Term = []
            mapped_Term.append((row["Mapped Term Label"], row["Mapping Score"]))
            ss.mapped_term_list.append(mapped_Term)
