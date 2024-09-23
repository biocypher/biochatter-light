import streamlit as st

ss = st.session_state

import requests
import pandas as pd
from io import StringIO


def fetch_csv_files():
    repo_url = "https://api.github.com/repos/marvinm2/pole/contents/data"

    if not ss.get("template_directory"):
        response = requests.get(repo_url)

        if response.status_code == 200:
            files = response.json()
            csv_files = [
                file["name"] for file in files if file["name"].endswith(".csv")
            ]
            ss.template_directory = csv_files
            return csv_files
        else:
            st.error("Error fetching data from the GitHub repository")
            return []

    else:
        return ss.template_directory


def read_csv_from_github(file_name):
    file_url = (
        f"https://raw.githubusercontent.com/marvinm2/pole/main/data/{file_name}"
    )
    response = requests.get(file_url)

    if response.status_code == 200:
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        return df
    else:
        st.error(f"Error fetching CSV file: {file_name}")
        return None


def filling_template_panel():
    """
    Display a panel that lists CSV files from the specified GitHub repository,
    allows the user to select one from a dropdown, and lets them add empty rows
    dynamically to the DataFrame with inline editing support.
    """
    st.markdown("### 📄 Select CSV File from GitHub Repository")

    csv_files = fetch_csv_files()

    if csv_files:
        selected_file = st.selectbox("Choose a CSV file:", csv_files)

        # Read the selected CSV file into a DataFrame
        df = read_csv_from_github(selected_file)

        if df is not None:
            if "df" not in st.session_state:
                st.session_state.df = df

            if st.button("Add Empty Row"):
                empty_row = pd.DataFrame(
                    [[None] * len(df.columns)], columns=df.columns
                )
                st.session_state.df = pd.concat(
                    [st.session_state.df, empty_row], ignore_index=True
                )

            st.markdown("### Editable DataFrame")
            edited_df = st.data_editor(st.session_state.df)

            st.session_state.df = edited_df

    else:
        st.warning("No CSV files available.")


filling_template_panel()
