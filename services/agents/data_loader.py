import pandas as pd
import streamlit as st
import re
from database import db_manager


# Define data loading functions
def load_agents_data():
    """Load agents data from database"""
    try:
        # Get all users with "agent" role
        users = db_manager.get_all_users()
        if users:
            df = pd.DataFrame(users)
            # Filter only agents
            agents_df = df[df['role_name'] == 'agent'].copy()
            # Convert dates
            if 'created_at' in agents_df.columns:
                agents_df['created_at'] = pd.to_datetime(agents_df['created_at'])
            if 'updated_at' in agents_df.columns:
                agents_df['updated_at'] = pd.to_datetime(agents_df['updated_at'])
            return agents_df
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['id', 'nin', 'name', 'email', 'role_name', 'is_active', 'created_at'])
    except Exception as e:
        st.error(f"Error loading agents: {str(e)}")
        return pd.DataFrame(columns=['id', 'nin', 'name', 'email', 'role_name', 'is_active', 'created_at'])

def load_roles_data():
    """Load roles data from database"""
    try:
        roles = db_manager.get_all_roles()
        return roles if roles else []
    except Exception as e:
        st.error(f"Error loading roles: {str(e)}")
        return []

def is_valid_email(email):
    """Validates email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None
