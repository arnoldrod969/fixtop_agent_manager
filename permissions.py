"""
Module de gestion des permissions basées sur les rôles
"""

import streamlit as st
from typing import Dict, List, Tuple

class PermissionManager:
    """Gestionnaire des permissions basées sur les rôles"""
    
    # Configuration des permissions par rôle
    ROLE_PERMISSIONS = {
        'admin': {
            'user_page': {
                'can_view': True,
                'can_add': True,
                'can_edit': True,
                'can_delete': True,
                'can_view_stats': True,
                'can_view_all': True
            },
            'manager_page': {
                'can_view': True,
                'can_add': True,
                'can_edit': True,
                'can_delete': True,
                'can_view_stats': True,
                'can_view_all': True
            },
            'agent_page': {
                'can_view': True,
                'can_add': True,
                'can_edit': True,
                'can_delete': True,
                'can_view_stats': True,
                'can_view_all': True
            },
            'ticket_page': {
                'can_view': True,
                'can_add': False,       # Admin peut seulement voir et consulter les stats
                'can_edit': False,
                'can_delete': False,
                'can_view_stats': True,
                'can_view_all': True
            }
        },
        'manager': {
            'user_page': {
                'can_view': False,  # Pas d'accès à la gestion des utilisateurs
                'can_add': False,
                'can_edit': False,
                'can_delete': False,
                'can_view_stats': False,
                'can_view_all': False
            },
            'manager_page': {
                'can_view': True,   # Peut voir ses propres infos
                'can_add': False,   # Ne peut pas créer d'autres managers
                'can_edit': True,   # Peut éditer ses propres infos
                'can_delete': False,
                'can_view_stats': False,
                'can_view_all': False  # Voit seulement ses propres infos
            },
            'agent_page': {
                'can_view': True,
                'can_add': True,    # Peut créer des agents
                'can_edit': True,   # Peut modifier des agents
                'can_delete': False,
                'can_view_stats': True,
                'can_view_all': True
            },
            'ticket_page': {
                'can_view': True,
                'can_add': True,       # Manager peut seulement voir et consulter les stats
                'can_edit': True,
                'can_delete': False,
                'can_view_stats': True,
                'can_view_all': True
            }
        },
        'agent': {
            'user_page': {
                'can_view': False,  # Pas d'accès à la gestion des utilisateurs
                'can_add': False,
                'can_edit': False,
                'can_delete': False,
                'can_view_stats': False,
                'can_view_all': False
            },
            'manager_page': {
                'can_view': False,  # Pas d'accès à la gestion des managers
                'can_add': False,
                'can_edit': False,
                'can_delete': False,
                'can_view_stats': False,
                'can_view_all': False
            },
            'agent_page': {
                'can_view': True,   # Peut voir ses propres infos
                'can_add': False,   # Ne peut pas créer d'autres agents
                'can_edit': True,   # Peut éditer ses propres infos
                'can_delete': False,
                'can_view_stats': False,
                'can_view_all': False  # Voit seulement ses propres infos
            },
            'ticket_page': {
                'can_view': True,
                'can_add': True,        # Agent peut tout faire sur les tickets
                'can_edit': True,
                'can_delete': True,
                'can_view_stats': True,
                'can_view_all': True
            }
        }
    }
    
    @staticmethod
    def get_user_role() -> str:
        """Récupère le rôle de l'utilisateur connecté"""
        return st.session_state.get('user_role', 'agent')
    
    @staticmethod
    def get_user_id() -> int:
        """Récupère l'ID de l'utilisateur connecté"""
        return st.session_state.get('user_id', None)
    
    @staticmethod
    def has_permission(page: str, action: str) -> bool:
        """Vérifie si l'utilisateur a la permission pour une action sur une page"""
        user_role = PermissionManager.get_user_role()
        
        if user_role not in PermissionManager.ROLE_PERMISSIONS:
            return False
            
        page_permissions = PermissionManager.ROLE_PERMISSIONS[user_role].get(page, {})
        return page_permissions.get(action, False)
    
    @staticmethod
    def check_page_access(page: str) -> bool:
        """Vérifie si l'utilisateur peut accéder à une page"""
        return PermissionManager.has_permission(page, 'can_view')
    
    @staticmethod
    def get_available_tabs(page: str) -> List[str]:
        """Retourne les onglets disponibles pour l'utilisateur sur une page donnée"""
        user_role = PermissionManager.get_user_role()
        
        if not PermissionManager.has_permission(page, 'can_view'):
            return []
        
        available_tabs = ["📋 List"]
        
        if PermissionManager.has_permission(page, 'can_add'):
            available_tabs.append("➕ Add")
            
        if PermissionManager.has_permission(page, 'can_edit'):
            available_tabs.append("✏️ Edit")
            
        if PermissionManager.has_permission(page, 'can_delete'):
            available_tabs.append("🗑️ Delete")
            
        if PermissionManager.has_permission(page, 'can_view_stats'):
            available_tabs.append("📊 Statistics")
            
        return available_tabs
    
    @staticmethod
    def show_access_denied(message: str = None):
        """Displays an access denied message"""
        default_message = "🚫 Access denied - You don't have the necessary permissions to access this functionality."
        st.error(message or default_message)
        st.info("Contact your administrator if you think this is an error.")
        st.stop()
    
    @staticmethod
    def filter_data_by_user(data, user_id_column: str = 'id'):
        """Filtre les données pour ne montrer que celles de l'utilisateur connecté (si pas admin/manager avec accès complet)"""
        user_role = PermissionManager.get_user_role()
        user_id = PermissionManager.get_user_id()
        
        # Si l'utilisateur peut voir toutes les données, retourner toutes
        if user_role == 'admin':
            return data
            
        # Pour les managers et agents, filtrer selon les permissions
        if user_role == 'manager':
            # Le manager peut voir tous les agents mais seulement ses propres infos manager
            return data
        elif user_role == 'agent':
            # L'agent ne voit que ses propres données
            if user_id and not data.empty:
                return data[data[user_id_column] == user_id]
            
        return data
    
    @staticmethod
    def can_edit_user(target_user_id: int, target_user_role: str = None) -> bool:
        """Vérifie si l'utilisateur connecté peut éditer un autre utilisateur"""
        user_role = PermissionManager.get_user_role()
        user_id = PermissionManager.get_user_id()
        
        # Admin peut tout éditer
        if user_role == 'admin':
            return True
            
        # Manager peut éditer les agents et ses propres infos
        if user_role == 'manager':
            if user_id == target_user_id:  # Ses propres infos
                return True
            if target_user_role == 'agent':  # Peut éditer les agents
                return True
            return False
            
        # Agent peut seulement éditer ses propres infos
        if user_role == 'agent':
            return user_id == target_user_id
            
        return False

# Instance globale du gestionnaire de permissions
permission_manager = PermissionManager()