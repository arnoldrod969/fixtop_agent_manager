import streamlit as st
import sys
import os
from components.users import tabs_list , tabs_add , tabs_edit , tabs_delete , tabs_statistics
from components.sidebar import show_sidebar

# Add parent directory to path to import database and permissions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from permissions import PermissionManager

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")  # Redirect to home/login if not connected

show_sidebar()

# Check page access permissions
if not PermissionManager.check_page_access('user_page'):
    PermissionManager.show_access_denied("This page is reserved for administrators.")

"""User management page"""
st.title("👥 User Management")

# Get available tabs according to permissions
available_tabs = PermissionManager.get_available_tabs('user_page')

if not available_tabs:
    st.error("No tabs available for your role.")
    st.stop()

# Create tabs dynamically
tabs = st.tabs(available_tabs)


# Load roles globally for reuse
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
