import streamlit as st
from database import db_manager
from permissions import PermissionManager

# Utility functions
@st.cache_data(ttl=60)
def load_tickets():
    """Loads all tickets from the database"""
    return db_manager.get_all_problems()

@st.cache_data(ttl=60)
def load_editable_tickets():
    """Loads tickets that the current user can edit based on their role"""
    try:
        # Récupérer l'utilisateur connecté et son rôle
        current_user_id = PermissionManager.get_user_id()
        current_user_role = PermissionManager.get_user_role()
        
        if not current_user_id:
            return []
        
        # Récupérer tous les tickets
        all_tickets = db_manager.get_all_problems()
        
        # Filtrer selon les permissions d'édition
        if current_user_role == 'admin':
            # Admin peut éditer tous les tickets (mais selon les permissions, admin ne peut pas éditer)
            return all_tickets
        elif current_user_role == 'manager':
            # Manager peut éditer tous les tickets (mais selon les permissions, manager ne peut pas éditer)
            return all_tickets
        elif current_user_role == 'agent':
            # Agent peut seulement éditer les tickets qu'il a créés
            editable_tickets = []
            for ticket in all_tickets:
                if ticket.get('created_by') == current_user_id:
                    editable_tickets.append(ticket)
            return editable_tickets
        
        return []
        
    except Exception as e:
        st.error(f"Error loading editable tickets: {str(e)}")
        return []

@st.cache_data(ttl=60)
def load_deletable_tickets():
    """Loads tickets that the current user can delete based on their role"""
    try:
        # Récupérer l'utilisateur connecté
        current_user_id = PermissionManager.get_user_id()
        if not current_user_id:
            return []
        
        # Récupérer tous les tickets
        all_tickets = db_manager.get_all_problems()
        
        # Filtrer selon les permissions de suppression
        deletable_tickets = []
        for ticket in all_tickets:
            can_delete, reason = db_manager.can_delete_ticket(current_user_id, ticket['created_by'])
            if can_delete:
                deletable_tickets.append(ticket)
        
        return deletable_tickets
        
    except Exception as e:
        st.error(f"Error loading deletable tickets: {str(e)}")
        return []

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
