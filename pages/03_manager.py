import streamlit as st
import sys
import os

from components.sidebar import show_sidebar
from components.manager import tabs_list , tabs_add , tabs_edit , tabs_statistics

# Ajouter le répertoire parent au path pour importer database et permissions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from permissions import PermissionManager

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")  # Redirect to home/login if not connected

show_sidebar()

# Check page access permissions
if not PermissionManager.check_page_access('manager_page'):
    PermissionManager.show_access_denied("You do not have the necessary permissions to access this page.")

"""Manager management page"""
st.title("👨‍💼 Manager Management")

# Get available tabs according to permissions
available_tabs = PermissionManager.get_available_tabs('manager_page')

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
        #elif "Delete" in tab_name:
        #    tabs_delete.display()
        elif "Statistics" in tab_name:
            tabs_statistics.display()
