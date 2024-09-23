import streamlit as st

ss = st.session_state
import requests
import pandas as pd
from io import StringIO
import os


def fetch_csv_files():
    repo_url = os.getenv("FILLING_TEMPLATE_API_URL")
    st.write(repo_url)

    if not repo_url:
        st.error(
            "Environment variable 'FILLING_TEMPLATE_API_URL' is not set. "
            "Please set it to a valid GitHub API address of a folder "
            "containing your CSV templates to continue."
        )
        return []

    if not ss.get("template_directory"):
        response = requests.get(repo_url)

        if response.status_code == 200:
            files = response.json()
            # Fetch the file names and download URLs from the response
            csv_files = [
                {"name": file["name"], "download_url": file["download_url"]}
                for file in files
                if file["name"].endswith(".csv")
            ]
            ss.template_directory = csv_files
            return csv_files
        else:
            st.error("Error fetching data from the GitHub repository")
            return []

    else:
        return ss.template_directory


def read_csv_from_github(file_info):
    file_url = file_info["download_url"]

    response = requests.get(file_url)
    st.write(f"Fetching file from {file_url}")
    if response.status_code == 200:
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        return df
    else:
        st.error(f"Error fetching CSV file: {file_info['name']}")
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
        # Track the selected file in session state
        selected_file = st.selectbox(
            "Choose a CSV file:", csv_files, format_func=lambda x: x["name"]
        )

        # Check if a new file is selected, reset the DataFrame if necessary
        if "selected_file" not in ss or ss.selected_file != selected_file:
            ss.selected_file = selected_file  # Update selected file
            ss.df = read_csv_from_github(
                selected_file
            )  # Load new CSV into DataFrame

        if ss.df is not None:
            if st.button("Add Empty Row"):
                empty_row = pd.DataFrame(
                    [[None] * len(ss.df.columns)], columns=ss.df.columns
                )
                ss.df = pd.concat([ss.df, empty_row], ignore_index=True)

            st.markdown("### Editable DataFrame")
            edited_df = st.data_editor(ss.df)

            ss.df = edited_df

    else:
        st.warning("No CSV files available.")
