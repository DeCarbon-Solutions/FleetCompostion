import streamlit as st
import math
import pandas as pd
import plotly.express as px

# --- Configuration & Route Specific Data ---

YEAR_OPTIONS = [2030, 2040, 2050]

ROUTE_PARAMS = {
    "Brazil to China (Crude Oil)": {
        "divisor": 9.95,
        "new_builds": 18,
        "existing": 0
    },
    "Brazil to Singapore (Crude Oil)": {
        "divisor": 6.42,
        "new_builds": 10,
        "existing": 10
    },
    "Brazil to SE Asia (Oil Product)": {
        "divisor": 6.42,
        "new_builds": 9,
        "existing": 0
    }
}
ROUTE_OPTIONS = list(ROUTE_PARAMS.keys())

# --- Initialize Session State ---
if 'calculated_results' not in st.session_state:
    st.session_state.calculated_results = None
if 'show_results' not in st.session_state: # Flag to control result display persistence
    st.session_state.show_results = False

# --- Callback to clear results if inputs change ---
def clear_results():
    st.session_state.calculated_results = None
    st.session_state.show_results = False

# --- App Layout ---

st.set_page_config(layout="centered")

st.title("Shipping Vessel Composition Calculator")
st.markdown("Estimate Petrobras Fleet Composition based on route and export volume.")
st.divider()

# --- Input Section ---
st.subheader("1. Select Parameters")

col1, col2 = st.columns(2)

with col1:
    selected_year = st.selectbox(
        "Select Target Year:",
        options=YEAR_OPTIONS,
        key='year_select',
        on_change=clear_results # Clear results if year changes
    )
    selected_route = st.selectbox(
        "Select Shipping Route:",
        options=ROUTE_OPTIONS,
        key='route_select',
        on_change=clear_results # Clear results if route changes
    )

with col2:
    export_volume = st.number_input(
        "Cargo Export Volume (MM bbl/year):",
        min_value=0.0,
        value=289.4,
        step=10.0,
        format="%.2f",
        key='volume_input',
        help="Enter the total millions of barrels exported annually on this route.",
        on_change=clear_results # Clear results if volume changes
    )

st.divider()

# --- Calculation Trigger ---
if st.button("Calculate Vessel Requirements", type="primary"):
    if export_volume <= 0:
        st.error("Please enter a positive Cargo Export Volume.")
        clear_results() # Ensure results area is cleared
    elif selected_route not in ROUTE_PARAMS:
         st.error("Invalid route selected. Please choose from the list.")
         clear_results() # Ensure results area is cleared
    else:
        # --- Perform Calculations ---
        params = ROUTE_PARAMS[selected_route]
        divisor = params["divisor"]
        fixed_new_builds = params["new_builds"]
        fixed_existing = params["existing"]

        total_vessels = math.ceil(export_volume / divisor)
        new_builds_needed = fixed_new_builds
        existing_vessels = fixed_existing
        charter_needed = max(0, total_vessels - new_builds_needed - existing_vessels)

        # Store results in session state
        st.session_state.calculated_results = {
            "selected_year": selected_year,
            "selected_route": selected_route,
            "export_volume": export_volume,
            "Total Vessels Required": total_vessels, # Use descriptive keys
            "New Building Needed (Fixed)": new_builds_needed,
            "Existing Vessels (Fixed)": existing_vessels,
            "Charter Vessels Needed": charter_needed
        }
        st.session_state.show_results = True # Set flag to show results area

st.divider()

# --- Output Section ---
st.subheader("2. Calculated Results")

# Display results only if the flag is true and results exist
if st.session_state.show_results and st.session_state.calculated_results:
    results = st.session_state.calculated_results

    st.markdown(f"""
    **Based on Inputs:**
    - **Year:** {results['selected_year']}
    - **Route:** {results['selected_route']}
    - **Export Volume:** {results['export_volume']:.2f} MM bbl/year
    """)
    st.markdown("---")

    # --- Create Bar Chart ---
    # Prepare data for Plotly
    vessel_types = [
        "Total Vessels Required",
        "Existing Vessels (Fixed)",
        "New Building Needed (Fixed)",
        "Charter Vessels Needed"
    ]
    vessel_counts = [
        results["Total Vessels Required"],
        results["Existing Vessels (Fixed)"],
        results["New Building Needed (Fixed)"],
        results["Charter Vessels Needed"]
    ]

    chart_data = pd.DataFrame({
        "Vessel Category": vessel_types,
        "Number of Vessels": vessel_counts
    })

    # Define the specific order for the x-axis categories
    category_order = [
        "Total Vessels Required",
        "Existing Vessels (Fixed)",
        "New Building Needed (Fixed)",
        "Charter Vessels Needed"
    ]
    chart_data['Vessel Category'] = pd.Categorical(
        chart_data['Vessel Category'],
        categories=category_order,
        ordered=True
    )
    chart_data = chart_data.sort_values('Vessel Category')


    # Create the bar chart
    fig = px.bar(
        chart_data,
        x="Vessel Category",
        y="Number of Vessels",
        title="Vessel Requirement Breakdown",
        text="Number of Vessels", # Display values on bars
        labels={"Number of Vessels": "Count", "Vessel Category": "Category"}, # Nicer axis labels
        color_discrete_sequence=px.colors.qualitative.Pastel1 # Example color scheme
    )

    # Customize layout
    fig.update_layout(
        xaxis_title=None, # Remove x-axis title if categories are clear
        yaxis_title="Number of Vessels",
        plot_bgcolor='rgba(0,0,0,0)', # Transparent background
        yaxis_gridcolor='lightgrey',
         uniformtext_minsize=8, # Ensure text fits
         uniformtext_mode='hide' # Hide text if it doesn't fit
    )
    # Improve text appearance
    fig.update_traces(
        texttemplate='%{text:.0f}', # Format text as integer
        textposition='outside' # Position text outside bars
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

    # Calculation details are now omitted as requested

else:
    # Show this message only if the button hasn't been clicked yet in this session
    # or if inputs were invalid on the last click
    if not st.session_state.show_results:
        st.info("Click 'Calculate Vessel Requirements' after entering parameters.")


# --- Footer ---
st.divider()
st.caption("Disclaimer: Calculations based on 050 project pre-calculation of minimum export volume (2025-2050) per route.")
