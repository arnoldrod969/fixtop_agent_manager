import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import random
import re
import time
from components.agents import tabs_list, tabs_add, tabs_edit, tabs_delete, tabs_statistics
from components.sidebar import show_sidebar
from services.agents.data_loader import load_roles_data

# Add parent directory to path to import database and permissions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from permissions import PermissionManager

# Email validation function

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")  # Redirect to home/login if not connected

show_sidebar()

# Check page access permissions
if not PermissionManager.check_page_access('agent_page'):
    PermissionManager.show_access_denied("You do not have the necessary permissions to access this page.")

"""Agent management page"""
st.title("🤖 Agent Management")

# Get available tabs according to permissions
available_tabs = PermissionManager.get_available_tabs('agent_page')

if not available_tabs:
    st.error("No tabs available for your role.")
    st.stop()

# Create tabs dynamically
tabs = st.tabs(available_tabs)




for i, tab_name in enumerate(available_tabs):
    with tabs[i]:
        if "List" in tab_name:
            tabs_list.display()
        elif "Add" in tab_name:
            tabs_add.display()
        elif "Edit" in tab_name:
            tabs_edit.display()
        elif "Delete" in tab_name:
            tabs_delete.display()
        elif "Statistics" in tab_name:
            tabs_statistics.display()

