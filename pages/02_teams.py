import streamlit as st
import sys
import os
import re
from components.teams import tabs_list , tabs_add , tabs_delete , tabs_edit , tabs_statistics
from components.sidebar import show_sidebar

# Add parent directory to path to import database and permissions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import db_manager
from permissions import PermissionManager


# Email validation function
def is_valid_email(email):
    """Validates email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")  # Redirect to home/login if not connected

show_sidebar()

# Check page access permissions
if not PermissionManager.check_page_access('teams_page'):
    PermissionManager.show_access_denied("You do not have the necessary permissions to access this page.")

"""Team management page"""
st.title("🤖 Team Management")

# Get available tabs according to permissions
available_tabs = PermissionManager.get_available_tabs('teams_page')

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

