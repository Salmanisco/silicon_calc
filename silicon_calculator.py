import streamlit as st
import pandas as pd
import math
import io
from typing import Tuple

# --- Helper Functions ---

def calculate_project_materials(
    df: pd.DataFrame, 
    ext_width_mm: float, ext_depth_mm: float, ext_can_vol_ml: float,
    int_width_mm: float, int_depth_mm: float, int_can_vol_ml: float,
    screw_spacing_cm: float,
    waste_factor_percent: float
) -> Tuple[pd.DataFrame, float, float, float, int, int, int, float]:
    """
    Calculates the silicone and hardware needs for a project.

    Returns:
        A tuple containing:
        - The modified DataFrame.
        - Total project perimeter (meters).
        - Exterior Silicone Length (meters).
        - Interior Silicone Length (meters).
        - Exterior Cans Needed (int).
        - Interior Cans Needed (int).
        - Total Screws Needed (int).
        - Total Rubber Length (meters).
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
    
    # 4. Apply Waste Factor Multiplier
    waste_multiplier = (1 + waste_factor_percent / 100)

    # --- Exterior Calculation ---
    total_ext_length = total_project_perimeter * waste_multiplier
    
    ext_vol_per_meter_ml = ext_width_mm * ext_depth_mm
    if ext_vol_per_meter_ml > 0:
        ext_meters_per_can = ext_can_vol_ml / ext_vol_per_meter_ml
        ext_cans = math.ceil(total_ext_length / ext_meters_per_can)
    else:
        ext_cans = 0

    # --- Interior Calculation ---
    total_int_length = total_project_perimeter * waste_multiplier
    
    int_vol_per_meter_ml = int_width_mm * int_depth_mm
    if int_vol_per_meter_ml > 0:
        int_meters_per_can = int_can_vol_ml / int_vol_per_meter_ml
        int_cans = math.ceil(total_int_length / int_meters_per_can)
    else:
        int_cans = 0
        
    # --- Screw Calculation ---
    if screw_spacing_cm > 0:
        spacing_m = screw_spacing_cm / 100.0
        total_screws = math.ceil(total_project_perimeter / spacing_m)
    else:
        total_screws = 0
        
    # --- Rubber Calculation ---
    # Perimeter * 3 * Waste Factor
    total_rubber_length = total_project_perimeter * 3 * waste_multiplier

    return (
        df,
        total_project_perimeter,
        total_ext_length,
        total_int_length,
        ext_cans,
        int_cans,
        total_screws,
        total_rubber_length
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

from datetime import datetime
from fpdf import FPDF

def generate_pdf_report(
    project_id: str,
    total_perimeter: float,
    ext_data: dict,
    int_data: dict,
    hardware_data: dict,
    df: pd.DataFrame
) -> bytes:
    """Generates a PDF report for the project."""
    
    class PDF(FPDF):
        def header(self):
            self.set_font('helvetica', 'B', 16)
            self.cell(0, 10, 'Procurement Requirement Report', border=False, align='C')
            self.ln(20)

        def footer(self):
            self.set_y(-15)
            self.set_font('helvetica', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_font('helvetica', '', 12)
    
    # --- Project Info ---
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(40, 10, 'Project ID:', border=False)
    pdf.set_font('helvetica', '', 12)
    pdf.cell(0, 10, project_id if project_id else "Untitled Project", border=False, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(40, 10, 'Date:', border=False)
    pdf.set_font('helvetica', '', 12)
    pdf.cell(0, 10, datetime.now().strftime("%Y-%m-%d %H:%M"), border=False, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    # --- Summary Section ---
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, 'Material Summary', border="B", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font('helvetica', '', 12)
    
    # Total Perimeter
    pdf.cell(60, 10, 'Total Window Perimeter:', border=False)
    pdf.cell(0, 10, f"{total_perimeter:.1f} m", border=False, new_x="LMARGIN", new_y="NEXT")
    
    # Exterior
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, 'Exterior Silicone (Outside)', border=False, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', '', 12)
    pdf.cell(10) # Indent
    pdf.cell(50, 10, f"- Cans Needed:", border=False)
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, f"{ext_data['cans']} Cans ({ext_data['vol']}ml)", border=False, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', '', 12)
    pdf.cell(10)
    pdf.cell(50, 10, f"- Joint Size:", border=False)
    pdf.cell(0, 10, f"{ext_data['width']}mm x {ext_data['depth']}mm", border=False, new_x="LMARGIN", new_y="NEXT")

    # Interior
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, 'Interior Silicone (Inside)', border=False, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', '', 12)
    pdf.cell(10) # Indent
    pdf.cell(50, 10, f"- Cans Needed:", border=False)
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, f"{int_data['cans']} Cans ({int_data['vol']}ml)", border=False, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', '', 12)
    pdf.cell(10)
    pdf.cell(50, 10, f"- Joint Size:", border=False)
    pdf.cell(0, 10, f"{int_data['width']}mm x {int_data['depth']}mm", border=False, new_x="LMARGIN", new_y="NEXT")
    
    # Hardware
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, 'Hardware & Rubber', border=False, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', '', 12)
    pdf.cell(10) # Indent
    pdf.cell(50, 10, f"- Screws Needed:", border=False)
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, f"{hardware_data['screws']} pcs", border=False, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', '', 12)
    pdf.cell(10) 
    pdf.cell(50, 10, f"- Rubber Gasket:", border=False)
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, f"{hardware_data['rubber']:.1f} m", border=False, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.set_font('helvetica', 'I', 10)
    waste_txt = f"Note: Calculations include a {hardware_data['waste']}% waste factor."
    pdf.multi_cell(0, 10, waste_txt)
    
    return bytes(pdf.output())

# --- Main App ---

def main():
    st.set_page_config(page_title="Silicone & Hardware Calculator", page_icon="🪟", layout="wide")
    initialize_state()

    st.title("🪟 Silicone & Hardware Calculator")
    st.markdown(
        "Calculate silicone cans and screws needed for window installation. "
        "Separated by **Inside** and **Outside** for silicone."
    )

    # --- Sidebar: Global Settings ---
    st.sidebar.header("Project Settings")
    
    with st.sidebar.expander("🔩 Hardware / Screws", expanded=True):
        screw_spacing = st.number_input(
             "Screw Spacing (cm)", min_value=10.0, value=40.0, step=5.0, 
             help="Distance between fastening screws along the perimeter."
        )

    waste_factor = st.sidebar.slider(
        "Waste Factor (%)",
        min_value=0,
        max_value=30,
        value=10,
        help="Add a percentage to account for waste, tube changes, and over-application.",
    )
    
    st.sidebar.divider()
    
    # --- EXTERIOR TAB ---
    with st.sidebar.expander("🧱 Exterior / Outside", expanded=True):
        st.markdown("**Exterior Joint Dimensions**")
        ext_width = st.number_input(
            "Ext. Gap Width (mm)", min_value=1.0, value=5.0, step=0.5, key="ext_w"
        )
        ext_depth = st.number_input(
            "Ext. Gap Depth (mm)", min_value=1.0, value=5.0, step=0.5, key="ext_d"
        )
        
        st.markdown("**Exterior Can**")
        ext_can_vol = st.number_input(
            "Ext. Can Volume (ml)", min_value=100.0, value=600.0, step=10.0, key="ext_vol", help="e.g. 600ml sausage"
        )
        
        # Yield Check
        if ext_width > 0 and ext_depth > 0:
             yield_m = ext_can_vol / (ext_width * ext_depth)
             st.caption(f"Est. Yield: {yield_m:.1f} m/can")

    # --- INTERIOR TAB ---
    with st.sidebar.expander("🏠 Interior / Inside", expanded=True):
        st.markdown("**Interior Joint Dimensions**")
        int_width = st.number_input(
            "Int. Gap Width (mm)", min_value=1.0, value=5.0, step=0.5, key="int_w"
        )
        int_depth = st.number_input(
            "Int. Gap Depth (mm)", min_value=1.0, value=5.0, step=0.5, key="int_d"
        )
        
        st.markdown("**Interior Can**")
        int_can_vol = st.number_input(
            "Int. Can Volume (ml)", min_value=100.0, value=310.0, step=10.0, key="int_vol", help="e.g. 310ml cartridge"
        )

        # Yield Check
        if int_width > 0 and int_depth > 0:
             yield_m = int_can_vol / (int_width * int_depth)
             st.caption(f"Est. Yield: {yield_m:.1f} m/can")

    st.sidebar.divider()
    st.sidebar.info(
        "This app is for estimation purposes. Always confirm quantities on-site."
    )

    # --- Input Method Selection ---
    st.header("1. Input Window Data")
    
    # Project ID Input
    project_id = st.text_input("Project ID / Name", placeholder="e.g. Tower A - Floor 12")
    
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
            width="stretch",
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
                total_ext_length,
                total_int_length,
                ext_cans,
                int_cans,
                total_screws,
                total_rubber_length
            ) = calculate_project_materials(
                project_df, 
                ext_width, ext_depth, ext_can_vol,
                int_width, int_depth, int_can_vol,
                screw_spacing,
                waste_factor
            )

            st.subheader("Project Totals")
            
            # Create 4 columns for layout (Perimeter, Ext, Int, Hardware)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Project Perimeter", f"{total_project_perimeter:.1f} m")
                st.caption("Base length of all windows")
            
            with col2:
                st.info("🧱 Exterior Needs")
                st.metric("Total Length (w/ Waste)", f"{total_ext_length:.1f} m")
                st.success(f"**{ext_cans} Cans**")
                st.caption(f"Based on {ext_can_vol:.0f}ml can & {ext_width}x{ext_depth}mm gap")

            with col3:
                st.info("🏠 Interior Needs")
                st.metric("Total Length (w/ Waste)", f"{total_int_length:.1f} m")
                st.success(f"**{int_cans} Cans**")
                st.caption(f"Based on {int_can_vol:.0f}ml can & {int_width}x{int_depth}mm gap")
                
            with col4:
                st.warning("🔩 Hardware & Rubber")
                st.metric("Total Screws Needed", f"{total_screws}", help=f"1 screw every {screw_spacing} cm along the perimeter.")
                st.metric("Total Rubber Needed", f"{total_rubber_length:.1f} m", help="Perimeter × 3 (plus waste)")
                st.caption(f"Includes {waste_factor}% waste")
            
            # --- PDF Export Button ---
            pdf_bytes = generate_pdf_report(
                project_id,
                total_project_perimeter,
                ext_data={"cans": ext_cans, "vol": ext_can_vol, "width": ext_width, "depth": ext_depth},
                int_data={"cans": int_cans, "vol": int_can_vol, "width": int_width, "depth": int_depth},
                hardware_data={"screws": total_screws, "rubber": total_rubber_length, "waste": waste_factor},
                df=result_df
            )
            
            st.divider()
            st.download_button(
                label="📄 Download Procurement Report (PDF)",
                data=pdf_bytes,
                file_name=f"procurement_report_{project_id.replace(' ', '_') if project_id else 'project'}.pdf",
                mime="application/pdf"
            )

            st.divider()
            
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
            import traceback
            st.text(traceback.format_exc()) # Helping debug if pdf fails
    else:
        st.info("Add window types or upload a file to see the results.")

if __name__ == "__main__":
    main()
