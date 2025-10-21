from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from database import db_manager
from services.agents.data_loader import load_agents_data


def display():
    st.subheader("Agent Statistics")
    try:
        stats = db_manager.get_user_stats()
        # Load data
        agents_df = load_agents_data()
        # Filter for agents if necessary
        agent_stats = {k: v for k, v in stats.items() if k != 'by_role'}
        agent_by_role = [r for r in stats['by_role'] if r['name'] == 'agent']
        agent_stats['by_role'] = agent_by_role if agent_by_role else [{'name': 'agent', 'count': 0}]

        # Display statistics
        colx1, colx2, colx3, colx4 = st.columns(4)

        with colx1:
            total_agents = len(agents_df)
            st.metric("Total Agents", total_agents)

        with colx2:
            active_agents = len(agents_df[agents_df['is_active'] == 1])
            st.metric("Active Agents", active_agents)

        with colx3:
            inactive_agents = len(agents_df[agents_df['is_active'] == 0])
            st.metric("Inactive Agents", inactive_agents)

        with colx4:
            if not agents_df.empty and 'created_at' in agents_df.columns:
                recent_agents = len(agents_df[agents_df['created_at'] >= datetime.now() - timedelta(days=30)])
                st.metric("New (30d)", recent_agents)
            else:
                st.metric("New (30d)", 0)

        if agent_stats['by_role']:
            df_stats = pd.DataFrame(agent_stats['by_role'])
            st.subheader("Agents by Role")
            st.dataframe(df_stats)
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")
        st.info("Statistics feature to be implemented")