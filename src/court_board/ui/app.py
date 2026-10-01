import streamlit as st
from court_board.ui.state import AppState
from court_board.ui.components.import_component import render_import_page
from court_board.ui.components.classification_component import render_classification_page
from court_board.ui.components.stagewise_component import render_stagewise_page
from court_board.ui.components.routing_component import render_routing_page
from court_board.ui.components.final_board_component import render_final_board_page
from court_board.ui.components.export_component import render_export_page

st.set_page_config(
    page_title="Court Board Assistant",
    page_icon="⚖️",
    layout="wide"
)

# Initialize Session State
if "app_state" not in st.session_state or not hasattr(st.session_state["app_state"], "manual_stage_overrides"):
    st.session_state["app_state"] = AppState()

app_state = st.session_state["app_state"]
if not hasattr(app_state, "manual_stage_overrides"):
    app_state.manual_stage_overrides = {}

st.title("⚖️ COURT BOARD ASSISTANT")
st.caption("Daily Court Board & Stagewise Review System — Phase 7 GUI")

# Sidebar navigation
st.sidebar.title("Workflow Navigation")
page = st.sidebar.radio(
    "Select Step",
    [
        "1. Import Source",
        "2. Classification Review",
        "3. Stagewise Visualization",
        "4. Routing Review",
        "5. Final Board Preview",
        "6. Validation Gate & Export"
    ]
)

if page == "1. Import Source":
    render_import_page(app_state)
elif page == "2. Classification Review":
    render_classification_page(app_state)
elif page == "3. Stagewise Visualization":
    render_stagewise_page(app_state)
elif page == "4. Routing Review":
    render_routing_page(app_state)
elif page == "5. Final Board Preview":
    render_final_board_page(app_state)
elif page == "6. Validation Gate & Export":
    render_export_page(app_state)
