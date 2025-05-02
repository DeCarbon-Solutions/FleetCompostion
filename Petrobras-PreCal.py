import streamlit as st
import math
import pandas as pd
import plotly.express as px
import datetime

# --- Configuration ---

YEAR_OPTIONS = [2030, 2040, 2050]

# Route Information: Include divisors and display names
ROUTE_INFO = {
    "vlcc_china": {"display_name": "Brazil to China (Crude Oil)", "divisor": 9.95},
    "suez_seasia": {"display_name": "Brazil to SE Asia (Oil Product)", "divisor": 6.42},
    "suez_sing": {"display_name": "Brazil to Singapore (Crude Oil)", "divisor": 6.42},
    "afra_europe": {"display_name": "Brazil to Europe (Crude Oil)", "divisor": 6.42},
    "pana_houston": {"display_name": "Brazil to Houston (Crude Oil)", "divisor": 5.13},
    "mr_ny": {"display_name": "Brazil to New York (Oil Product)", "divisor": 3.69}
}
ROUTE_KEYS_ORDERED = ["vlcc_china", "suez_seasia", "suez_sing", "afra_europe", "pana_houston", "mr_ny"]

# *** Default Export Volumes ***
DEFAULT_EXPORT_VOLUMES = {
    "vlcc_china": 289.4,
    "suez_seasia": 95.8,
    "suez_sing": 123.3,
    "afra_europe": 209.2,
    "pana_houston": 45.2,
    "mr_ny": 91.7
}

# --- Helper Function for Year/Route Dependent Fixed Vessels ---

def get_fixed_vessels(route_key, year):
    """Determines the number of new builds and existing vessels based on route and year."""
    new_builds = 0
    existing = 0
    if route_key == "vlcc_china":
        if year == 2030: new_builds = 18; existing = 0
        elif year >= 2040: new_builds = 0; existing = 18
    elif route_key == "suez_sing":
        if year == 2030: new_builds = 10; existing = 10
        elif year == 2040: new_builds = 0; existing = 10
        elif year == 2050: new_builds = 0; existing = 17
    elif route_key == "suez_seasia":
        if year == 2030: new_builds = 9; existing = 0
        elif year == 2040: new_builds = 0; existing = 9
        elif year == 2050: new_builds = 0; existing = 12
    elif route_key == "afra_europe":
        if year == 2030 or year == 2040: new_builds = 0; existing = 5
    elif route_key == "pana_houston":
        if year == 2030: new_builds = 0; existing = 1
    elif route_key == "mr_ny":
        if year == 2030: new_builds = 0; existing = 4
    return new_builds, existing

# --- Initialize Session State ---
if 'selected_year' not in st.session_state:
    st.session_state.selected_year = YEAR_OPTIONS[0]

# *** Updated Initialization Loop for Volumes ***
for key in ROUTE_INFO.keys():
    vol_key = f"volume_{key}"
    if vol_key not in st.session_state:
        # Get the default volume for this specific route key
        st.session_state[vol_key] = DEFAULT_EXPORT_VOLUMES.get(key, 0.0) # Default to 0.0 if key missing

if 'calculated_results_all_routes' not in st.session_state:
    st.session_state.calculated_results_all_routes = None
if 'show_results' not in st.session_state:
    st.session_state.show_results = False

# --- Callback ---
def clear_results_on_year_change():
    st.session_state.calculated_results_all_routes = None
    st.session_state.show_results = False

# --- App Layout ---
st.set_page_config(layout="wide")
st.title("ABS EAL: Multi-Route Shipping Vessel Composition Calculator")
st.markdown("Estimate Fleet Composition based on export volumes for multiple routes.")
st.divider()

# --- Input Section ---
st.subheader("1. Select Target Year")
selected_year = st.selectbox(
    "Select Target Year:", options=YEAR_OPTIONS, key='year_select',
    on_change=clear_results_on_year_change
)
st.session_state.selected_year = selected_year # Update state
st.subheader("2. Enter Cargo Export Volumes (MM bbl/year)")
cols = st.columns(3)
col_idx = 0
for route_key in ROUTE_KEYS_ORDERED:
    vol_key = f"volume_{route_key}"
    route_display_name = ROUTE_INFO[route_key]["display_name"]
    with cols[col_idx]:
        # number_input will automatically use the default set in session state via 'key'
        st.number_input(
            f"Volume for {route_display_name}:", min_value=0.0, step=10.0,
            format="%.2f", key=vol_key, help=f"Enter volume for {route_display_name}."
        )
    col_idx = (col_idx + 1) % 3
st.divider()

# --- Calculation Trigger ---
if st.button("Calculate All Routes", type="primary"):
    all_volumes_valid = True
    for key in ROUTE_INFO.keys():
        if st.session_state[f"volume_{key}"] <= 0:
            st.warning(f"Enter positive volume for {ROUTE_INFO[key]['display_name']}.")
            all_volumes_valid = False; break
    if all_volumes_valid:
        results_dict = {}
        current_year = st.session_state.selected_year
        with st.spinner("Calculating..."):
            for key, info in ROUTE_INFO.items():
                volume = st.session_state[f"volume_{key}"]
                divisor = info["divisor"]
                new_builds, existing = get_fixed_vessels(key, current_year)
                total_vessels = math.ceil(volume / divisor)
                new_builds_needed = new_builds
                existing_vessels = existing
                charter_needed = max(0, total_vessels - new_builds_needed - existing_vessels)
                results_dict[key] = {
                    "route_display_name": info["display_name"],
                    "export_volume": volume,
                    "Total Vessels Required": total_vessels,
                    "New Building Needed": new_builds_needed,
                    "Existing Vessels": existing_vessels,
                    "Charter Vessels Needed": charter_needed
                }
        st.session_state.calculated_results_all_routes = results_dict
        st.session_state.show_results = True
        st.success("Calculations complete for all routes.")
    else:
        st.session_state.calculated_results_all_routes = None
        st.session_state.show_results = False
st.divider()

# --- Output Section ---
st.subheader("3. Calculated Results per Route")
if st.session_state.show_results and st.session_state.calculated_results_all_routes:
    all_results = st.session_state.calculated_results_all_routes
    out_cols = st.columns(3)
    out_col_idx = 0
    for route_key in ROUTE_KEYS_ORDERED:
        route_result = all_results.get(route_key)
        if route_result:
            with out_cols[out_col_idx]:
                st.markdown(f"**{route_result['route_display_name']}**")
                st.caption(f"Volume: {route_result['export_volume']:.2f} MM bbl/year")
                vessel_types = ["Total Vessels Required", "Existing Vessels", "New Building Needed", "Charter Vessels Needed"]
                vessel_counts = [route_result["Total Vessels Required"], route_result["Existing Vessels"], route_result["New Building Needed"], route_result["Charter Vessels Needed"]]
                chart_data = pd.DataFrame({"Category": vessel_types, "Number": vessel_counts})
                category_order = ["Total Vessels Required", "Existing Vessels", "New Building Needed", "Charter Vessels Needed"]
                chart_data['Category'] = pd.Categorical(chart_data['Category'], categories=category_order, ordered=True)
                chart_data = chart_data.sort_values('Category')
                fig = px.bar(
                    chart_data, x="Category", y="Number", text="Number",
                    labels={"Number": "Count"},
                    color_discrete_sequence=px.colors.qualitative.Pastel1
                )
                fig.update_layout(
                    xaxis_title=None, yaxis_title="Number of Vessels",
                    plot_bgcolor='rgba(0,0,0,0)', yaxis_gridcolor='lightgrey',
                    uniformtext_minsize=8, uniformtext_mode='hide',
                    margin=dict(l=10, r=10, t=20, b=10), height=350
                )
                fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
            out_col_idx = (out_col_idx + 1) % 3
else:
    if not st.session_state.show_results:
        st.info("Click 'Calculate All Routes' after entering export volumes.")

# --- Footer ---
st.divider()
current_year = datetime.datetime.now().year
st.caption(f"© {current_year} ABS EAL Lead: Dr. Chenxi Ji")
st.caption("Disclaimer: Calculations based on predefined rules and user inputs.")
