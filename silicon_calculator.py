import streamlit as st
import pandas as pd
import math
import io
from typing import Tuple

# --- Helper Functions ---

def calculate_silicone_needs(
    df: pd.DataFrame, meters_per_can: float, waste_factor_percent: float
) -> Tuple[pd.DataFrame, float, float, float, int]:
    """
    Calculates the silicone needs for a project.

    Args:
        df: DataFrame containing 'Width', 'Height', and 'Quantity'.
        meters_per_can: Meters of silicone provided by one can.
        waste_factor_percent: Percentage of waste to add (0-100).

    Returns:
        A tuple containing:
        - The modified DataFrame with calculation columns.
        - Total project perimeter (float).
        - Total silicone length needed (float).
        - Total silicone length with waste (float).
        - Total cans to buy (int).
    """
    # Ensure correct data types
    df = df.copy()
    df["Width"] = pd.to_numeric(df["Width"])
    df["Height"] = pd.to_numeric(df["Height"])
    df["Quantity"] = pd.to_numeric(df["Quantity"])

    # 1. Perimeter for one window
    df["Perimeter_Single"] = (df["Width"] + df["Height"]) * 2

    # 2. Total perimeter for all windows of that type
    df["Perimeter_Total_Type"] = df["Perimeter_Single"] * df["Quantity"]

    # 3. Sum for the whole project
    total_project_perimeter = df["Perimeter_Total_Type"].sum()

    # 4. Double it (for both sides)
    total_silicone_length = total_project_perimeter * 2

    # 5. Apply waste factor
    total_silicone_with_waste = total_silicone_length * (1 + waste_factor_percent / 100)

    # 6. Calculate cans needed (and round up)
    cans_needed_float = total_silicone_with_waste / meters_per_can
    total_cans_to_buy = math.ceil(cans_needed_float)

    return (
        df,
        total_project_perimeter,
        total_silicone_length,
        total_silicone_with_waste,
        total_cans_to_buy,
    )

def initialize_state():
    """Initializes session state for window list if it doesn't exist."""
    if "windows" not in st.session_state:
        st.session_state.windows = pd.DataFrame(
            [{"Width": 1.2, "Height": 1.5, "Quantity": 10}]
        )

@st.cache_data
def get_template_csv() -> str:
    """Generates a CSV template for download."""
    template_df = pd.DataFrame(
        {
            "Width": [1.2, 0.6, 2.0],
            "Height": [1.5, 0.6, 1.8],
            "Quantity": [10, 5, 8],
        }
    )
    buffer = io.StringIO()
    template_df.to_csv(buffer, index=False)
    return buffer.getvalue()

# --- Main App ---

def main():
    st.set_page_config(page_title="Silicone Calculator", page_icon="🪟", layout="wide")
    initialize_state()

    st.title("🪟 Silicone Can Calculator for Fabricators")
    st.markdown(
        "Calculate the total silicone cans needed for your window installation project. "
        "This tool accounts for applying silicone to **both sides** of the window perimeter."
    )

    # --- Sidebar: Global Settings ---
    st.sidebar.header("Project Settings")
    meters_per_can = st.sidebar.number_input(
        "Meters of Silicone per Can",
        min_value=1.0,
        value=12.0,
        step=0.5,
        help="Check your silicone can's label or estimate based on your typical bead size.",
    )

    waste_factor = st.sidebar.slider(
        "Waste Factor (%)",
        min_value=0,
        max_value=30,
        value=10,
        help="Add a percentage to account for waste, tube changes, and over-application.",
    )

    st.sidebar.divider()
    st.sidebar.info(
        "This app is for estimation purposes. Always confirm quantities on-site."
    )

    # --- Input Method Selection ---
    st.header("1. Input Window Data")
    input_method = st.radio(
        "Choose your input method:",
        ("Manually (for smaller projects)", "Upload a File (for massive projects)"),
        horizontal=True,
        label_visibility="collapsed",
    )

    project_df = None

    if input_method == "Manually (for smaller projects)":
        st.subheader("Manual Window Entry")
        st.markdown("Add, edit, or remove window types directly in the table below.")

        edited_df = st.data_editor(
            st.session_state.windows,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Width": st.column_config.NumberColumn(
                    "Width (meters)", min_value=0.1, step=0.1, format="%.2f", required=True
                ),
                "Height": st.column_config.NumberColumn(
                    "Height (meters)", min_value=0.1, step=0.1, format="%.2f", required=True
                ),
                "Quantity": st.column_config.NumberColumn(
                    "Quantity", min_value=1, step=1, format="%d", required=True
                ),
            },
        )
        st.session_state.windows = edited_df
        project_df = edited_df.copy()

    else:
        st.subheader("Upload Project File")
        st.download_button(
            label="Download Template CSV",
            data=get_template_csv(),
            file_name="window_project_template.csv",
            mime="text/csv",
        )
        st.markdown("Your file must have columns named `Width`, `Height`, and `Quantity`.")

        uploaded_file = st.file_uploader(
            "Upload your CSV or Excel file", type=["csv", "xlsx"]
        )

        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                if all(col in df.columns for col in ["Width", "Height", "Quantity"]):
                    st.success("File uploaded and read successfully!")
                    project_df = df.copy()
                else:
                    st.error(
                        "Error: Your file is missing one of the required columns: 'Width', 'Height', 'Quantity'."
                    )
            except Exception as e:
                st.error(f"An error occurred while reading the file: {e}")

    st.divider()

    # --- Calculation and Results ---
    st.header("2. Calculation Results")

    if project_df is not None and not project_df.empty:
        try:
            (
                result_df,
                total_project_perimeter,
                total_silicone_length,
                total_silicone_with_waste,
                total_cans_to_buy,
            ) = calculate_silicone_needs(project_df, meters_per_can, waste_factor)

            st.subheader("Project Totals")
            res_col1, res_col2, res_col3 = st.columns(3)
            res_col1.metric("Total Window Perimeter", f"{total_project_perimeter:.1f} m")
            res_col2.metric(
                "Total Silicone Length (Both Sides)", f"{total_silicone_length:.1f} m"
            )
            res_col3.metric(
                f"Total Length (with {waste_factor}% waste)",
                f"{total_silicone_with_waste:.1f} m",
            )

            st.divider()
            st.success(f"**Total Cans to Purchase: {total_cans_to_buy}**")
            st.caption(
                f"Calculation: {total_silicone_with_waste:.1f} meters needed / {meters_per_can} meters per can. Rounded up."
            )

            st.subheader("Project Data Summary")
            st.dataframe(
                result_df.style.format(
                    {
                        "Width": "{:.2f} m",
                        "Height": "{:.2f} m",
                        "Quantity": "{:,.0f}",
                        "Perimeter_Single": "{:.2f} m",
                        "Perimeter_Total_Type": "{:.2f} m",
                    }
                )
            )

        except Exception as e:
            st.error(f"An error occurred during calculation. Details: {e}")
    else:
        st.info("Add window types or upload a file to see the results.")

if __name__ == "__main__":
    main()
