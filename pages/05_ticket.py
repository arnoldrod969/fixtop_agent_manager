import streamlit as st
from permissions import PermissionManager
from components.sidebar import show_sidebar
from components.tickets import tabs_add, tabs_edit, tabs_list, tabs_delete, tabs_statistics

st.set_page_config(page_title="Ticket Management", page_icon="🎫", layout="wide")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")

show_sidebar()  # Gestion de la barre latérale

if not PermissionManager.check_page_access("ticket_page"):
    PermissionManager.show_access_denied("You do not have access to ticket management.")

st.title("🎫 Ticket Management")
st.markdown("---")

available_tabs = PermissionManager.get_available_tabs("ticket_page")
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
