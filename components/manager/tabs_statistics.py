import streamlit as st
import pandas as pd

from database import db_manager


def display():
    st.subheader("Manager Statistics")
    try:
        stats = db_manager.get_user_stats()
        # Filter for managers if necessary
        manager_stats = {k: v for k, v in stats.items() if k != 'by_role'}
        manager_by_role = [r for r in stats['by_role'] if r['name'] == 'manager']
        manager_stats['by_role'] = manager_by_role if manager_by_role else [{'name': 'manager', 'count': 0}]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Managers", manager_stats['total'])
        with col2:
            st.metric("Active", manager_stats['active'])
        with col3:
            st.metric("Inactive", manager_stats['inactive'])

        if manager_stats['by_role']:
            df_stats = pd.DataFrame(manager_stats['by_role'])
            st.subheader("Managers by Role")
            st.dataframe(df_stats)
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")
        st.info("Statistics feature to be implemented")