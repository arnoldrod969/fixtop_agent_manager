import streamlit as st
from database import db_manager

# Utility functions
@st.cache_data(ttl=60)
def load_tickets():
    """Loads all tickets from the database"""
    return db_manager.get_all_problems()

@st.cache_data(ttl=60)
def load_domains():
    """Loads all domains from the database"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name FROM craft 
                WHERE is_active = 1 
                ORDER BY name
            """
            )
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        st.error(f"Error loading domains: {str(e)}")
        return []


@st.cache_data(ttl=60)
def load_teams():
    """Loads all teams from the database"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name FROM team 
                WHERE is_active = 1 
                ORDER BY name
            """
            )
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        st.error(f"Error loading teams: {str(e)}")
        return []

@st.cache_data(ttl=60)
def load_specialties_by_domain(domain_id):
    """Loads specialties for the selected domain"""
    if not domain_id:
        return []
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name FROM speciality 
                WHERE craft_id = ? AND is_active = 1 
                ORDER BY name
            """,
                (domain_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        st.error(f"Error loading specialties: {str(e)}")
        return []

@st.cache_data(ttl=60)
def load_agents():
    """Loads all active agents from the database"""
    try:
        users = db_manager.get_all_users()
        if users:
            # Filter only active agents
            agents = [user for user in users if user['role_name'] == 'agent' and user['is_active'] == 1]
            return agents
        return []
    except Exception as e:
        st.error(f"Error loading agents: {str(e)}")
        return []
