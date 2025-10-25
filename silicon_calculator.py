import streamlit as st
import pandas as pd
import math
import io

# --- Page Configuration ---
st.set_page_config(page_title="Silicone Calculator", page_icon="🪟", layout="wide")

# --- Helper Functions for Manual Input ---


def initialize_state():
    """Initializes session state for window list if it doesn't exist."""
    if "windows" not in st.session_state:
        # Initialize with a DataFrame for st.data_editor
        st.session_state.windows = pd.DataFrame(
            [{"Width": 1.2, "Height": 1.5, "Quantity": 10}]
        )
    # 'next_id' is no longer needed


# --- The add_window_type and remove_window_type functions are no longer needed ---
# def add_window_type(): ... (REMOVE)
# def remove_window_type(window_id): ... (REMOVE)

# --- Initialize State ---
initialize_state()

# --- App Title ---
st.title("🪟 Silicone Can Calculator for Fabricators")
st.markdown(
    "Calculate the total silicone cans needed for your window installation project. This tool accounts for applying silicone to **both sides** of the window perimeter."
)

# --- Sidebar: Global Settings ---
st.sidebar.header("Project Settings")
meters_per_can = st.sidebar.number_input(
    "Meters of Silicone per Can",
    min_value=1.0,
    value=12.0,  # A reasonable default
    step=0.5,
    help="Check your silicone can's label or estimate based on your typical bead size (e.g., a 6mm bead might yield ~8-12m).",
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


# --- Main Page: Input Method Selection ---
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

    # --- Use st.data_editor for mobile-friendly input ---
    st.markdown("Add, edit, or remove window types directly in the table below.")

    edited_df = st.data_editor(
        st.session_state.windows,
        num_rows="dynamic",  # Allows adding/deleting rows
        use_container_width=True,
        column_config={
            "Width": st.column_config.NumberColumn(
                "Width (meters)",
                min_value=0.1,
                step=0.1,
                format="%.2f",
                required=True,
            ),
            "Height": st.column_config.NumberColumn(
                "Height (meters)",
                min_value=0.1,
                step=0.1,
                format="%.2f",
                required=True,
            ),
            "Quantity": st.column_config.NumberColumn(
                "Quantity",
                min_value=1,
                step=1,
                format="%d",
                required=True,
            ),
        },
    )

    # Update session state with the edited data
    st.session_state.windows = edited_df

    # Set project_df for calculation
    project_df = edited_df.copy()  # <-- Add .copy() here

else:
    # --- File Upload Method ---
    st.subheader("Upload Project File")

    # Provide a downloadable template
    @st.cache_data
    def get_template_csv():
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

            # --- Validate Uploaded DataFrame ---
            if all(col in df.columns for col in ["Width", "Height", "Quantity"]):
                st.success("File uploaded and read successfully!")
                project_df = df.copy()  # <-- And Add .copy() here
            else:
                st.error(
                    "Error: Your file is missing one of the required columns: 'Width', 'Height', 'Quantity'."
                )

        except Exception as e:
            st.error(f"An error occurred while reading the file: {e}")

# --- Divider ---
st.divider()

# --- 2. Calculation and Results ---
st.header("2. Calculation Results")

if project_df is not None and not project_df.empty:
    try:
        # Ensure correct data types
        project_df["Width"] = pd.to_numeric(project_df["Width"])
        project_df["Height"] = pd.to_numeric(project_df["Height"])
        project_df["Quantity"] = pd.to_numeric(project_df["Quantity"])

        # --- Core Calculation ---
        # 1. Perimeter for one window
        project_df["Perimeter_Single"] = (
            project_df["Width"] + project_df["Height"]
        ) * 2

        # 2. Total perimeter for all windows of that type
        project_df["Perimeter_Total_Type"] = (
            project_df["Perimeter_Single"] * project_df["Quantity"]
        )

        # 3. Sum for the whole project
        total_project_perimeter = project_df["Perimeter_Total_Type"].sum()

        # 4. Double it (for both sides)
        total_silicone_length = total_project_perimeter * 2

        # 5. Apply waste factor
        total_silicone_with_waste = total_silicone_length * (1 + waste_factor / 100)

        # 6. Calculate cans needed (and round up)
        cans_needed_float = total_silicone_with_waste / meters_per_can
        total_cans_to_buy = math.ceil(cans_needed_float)

        # --- Display Results ---
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

        # Final big result
        st.success(f"**Total Cans to Purchase: {total_cans_to_buy}**")
        st.caption(
            f"Calculation: {total_silicone_with_waste:.1f} meters needed / {meters_per_can} meters per can = {cans_needed_float:.2f} cans. Rounded up."
        )

        # --- Display Project Summary Table ---
        st.subheader("Project Data Summary")
        st.dataframe(
            project_df.style.format(
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
        st.error(
            f"An error occurred during calculation. Please check your inputs. Details: {e}"
        )

else:
    st.info("Add window types or upload a file to see the results.")
