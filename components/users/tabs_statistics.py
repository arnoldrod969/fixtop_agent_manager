import streamlit as st
import pandas as pd
from datetime import datetime
from services.tickets.data_loader import load_tickets, load_domains, load_teams, load_specialties_by_domain, load_agents
from services.tickets.export_utils import export_to_csv, export_to_pdf, export_to_excel
from services.cache_utils import clear_cache
from services.debug_logger import log_column_check, log_data_info


def display():
    st.subheader("Statistics")
    try:
        stats = db_manager.get_user_stats()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", stats['total'])
        with col2:
            st.metric("Active", stats['active'])
        with col3:
            st.metric("Inactive", stats['inactive'])

        if stats['by_role']:
            df_stats = pd.DataFrame(stats['by_role'])
            st.subheader("Users by Role")
            st.dataframe(df_stats)
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")
        st.info("Statistics feature to be implemented")