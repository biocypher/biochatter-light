import streamlit as st

ss = st.session_state

import requests
import pandas as pd
from io import StringIO
import os


def fetch_csv_files():
    # Check if the environment variable is set
    repo_url = os.getenv("FILLING_TEMPLATE_API_URL")
    st.write(repo_url)
    if not repo_url:
        st.error(
            "Environment variable 'FILLING_TEMPLATE_API_URL' is not set. Please set it to continue."
        )
        return []

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
    # Check if the environment variable is set
    base_url = os.getenv("FILLING_TEMPLATE_API_URL")
    if not base_url:
        st.error(
            "Environment variable 'FILLING_TEMPLATE_API_URL' is not set. Please set it to continue."
        )
        return None

    file_url = f"{base_url}/{file_name}"
    response = requests.get(file_url)
    st.write(file_url)
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

    # Fetch the CSV files only if the environment variable is set
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
