import streamlit as st
import pandas as pd
from database import db_manager

# Utility functions
@st.cache_data(ttl=60)
def load_teams_data():
    """Load teams data from database"""
    try:
        teams = db_manager.get_teams()
        if teams:
            df = pd.DataFrame(teams)
            # Convert dates
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
            if 'updated_at' in df.columns:
                df['updated_at'] = pd.to_datetime(df['updated_at'])
            return df
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['id', 'name', 'description', 'created_at', 'created_by'])
    except Exception as e:
        st.error(f"Error loading teams: {str(e)}")
        return pd.DataFrame(columns=['id', 'name', 'description', 'created_at', 'created_by'])

# Get available managers (users with manager role who are not already managing a team)
def get_available_managers():
    """Get managers who are not already assigned to a team"""
    try:
            all_users = db_manager.get_all_users()
            if all_users:
                # Filter for active managers
                managers = [user for user in all_users if
                            user['role_name'] == 'manager' and user['is_active'] == 1]

                # Check which managers are not already assigned to a team
                available_managers = []
                for manager in managers:
                    if db_manager.is_manager_available(manager['id']):
                        available_managers.append(manager)

                return available_managers
            return []
    except Exception as e:
        st.error(f"Error loading available managers: {str(e)}")
        return []
