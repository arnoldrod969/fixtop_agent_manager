import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import random
import re
import time

# Ajouter le répertoire parent au path pour importer database et permissions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import db_manager
from permissions import PermissionManager

# Fonction de validation d'email
def is_valid_email(email):
    """Valide le format d'un email"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")  # Redirige vers l'accueil/login si pas connecté

# Vérification des permissions d'accès à la page
if not PermissionManager.check_page_access('manager_page'):
    PermissionManager.show_access_denied("Vous n'avez pas les permissions nécessaires pour accéder à cette page.")

"""Page de gestion des managers"""
st.title("👨‍💼 Gestion des Managers")

# Définir les fonctions de chargement des données
def load_managers_data():
    """Charge les données des managers depuis la base de données"""
    try:
        # Récupérer tous les utilisateurs avec le rôle "manager"
        users = db_manager.get_all_users()
        if users:
            df = pd.DataFrame(users)
            # Filtrer uniquement les managers
            managers_df = df[df['role_name'] == 'manager'].copy()
            # Convertir les dates
            if 'created_at' in managers_df.columns:
                managers_df['created_at'] = pd.to_datetime(managers_df['created_at'])
            if 'updated_at' in managers_df.columns:
                managers_df['updated_at'] = pd.to_datetime(managers_df['updated_at'])
            return managers_df
        else:
            # Retourner un DataFrame vide avec les colonnes attendues
            return pd.DataFrame(columns=['id', 'nin', 'name', 'email', 'role_name', 'is_active', 'created_at'])
    except Exception as e:
        st.error(f"Erreur lors du chargement des managers : {str(e)}")
        return pd.DataFrame(columns=['id', 'nin', 'name', 'email', 'role_name', 'is_active', 'created_at'])

def load_roles_data():
    """Charge les données des rôles depuis la base de données"""
    try:
        roles = db_manager.get_all_roles()
        return roles if roles else []
    except Exception as e:
        st.error(f"Erreur lors du chargement des rôles : {str(e)}")
        return []

# Obtenir les onglets disponibles selon les permissions
available_tabs = PermissionManager.get_available_tabs('manager_page')

if not available_tabs:
    st.error("Aucun onglet disponible pour votre rôle.")
    st.stop()

# Créer les onglets dynamiquement
tabs = st.tabs(available_tabs)

# Charger les rôles globalement pour les réutiliser
roles = load_roles_data()

# Onglet Liste
if "📋 Liste" in available_tabs:
    tab_index = available_tabs.index("📋 Liste")
    with tabs[tab_index]:
        st.subheader("Liste des Managers")

        # Charger les données des managers
        managers_df = load_managers_data()
        
        # Dans l'onglet Liste, on affiche tous les managers pour tous les utilisateurs
        # (pas de filtrage par permissions ici)
        
        # Filtres et recherche
        col1, col2 = st.columns(2)

        with col1:
            search_manager = st.text_input("🔍 Rechercher", placeholder="Nom, email, ID...")

        with col2:
            status_filter = st.selectbox("Filtrer par statut", ["Tous", "Actif", "Inactif"])
        
        # Filtrer les données si nécessaire
        filtered_df = managers_df.copy()
        if not filtered_df.empty:
            # Filtre par recherche (nom, email, ID)
            if search_manager.strip():
                search_term = search_manager.strip().lower()
                filtered_df = filtered_df[
                    filtered_df['name'].str.lower().str.contains(search_term, na=False) |
                    filtered_df['email'].str.lower().str.contains(search_term, na=False) |
                    filtered_df['id'].astype(str).str.contains(search_term, na=False)
                ]
            
            # Filtre par statut
            if status_filter != "Tous":
                if status_filter == "Actif":
                    filtered_df = filtered_df[filtered_df['is_active'] == 1]
                elif status_filter == "Inactif":
                    filtered_df = filtered_df[filtered_df['is_active'] == 0]
            
            # Préparer les données pour l'affichage
            display_df = filtered_df.copy()
            if not display_df.empty:
                display_df['Statut'] = display_df['is_active'].apply(lambda x: "Actif" if x == 1 else "Inactif")
                display_df = display_df[['id', 'nin', 'name', 'email', 'role_name', 'Statut', 'created_at']]
                display_df.columns = ['ID', 'NIN', 'Nom', 'Email', 'Rôle', 'Statut', 'Date création']
                display_df = display_df.reset_index(drop=True)  # Réinitialiser l'index pour éviter les faux IDs
        else:
            display_df = pd.DataFrame(columns=['ID', 'NIN', 'Nom', 'Email', 'Rôle', 'Statut', 'Date création'])

        # Système de pagination
        if not display_df.empty:
            total_managers = len(display_df)
            
            # Configuration de la pagination
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.info(f"📊 **{total_managers}** manager(s) trouvé(s)")
            
            with col2:
                managers_per_page = st.selectbox(
                    "Managers par page", 
                    [10, 25, 50, 100], 
                    index=1,  # Par défaut 25
                    key="managers_per_page_list"
                )
            
            with col3:
                total_pages = max(1, (total_managers - 1) // managers_per_page + 1)
                current_page = st.number_input(
                    f"Page (1-{total_pages})", 
                    min_value=1, 
                    max_value=total_pages, 
                    value=1,
                    key="current_page_managers"
                )
            
            # Calculer les indices pour la pagination
            start_idx = (current_page - 1) * managers_per_page
            end_idx = min(start_idx + managers_per_page, total_managers)
            
            # Afficher les données paginées
            paginated_df = display_df.iloc[start_idx:end_idx]
            
            # Afficher les informations de pagination
            st.caption(f"Affichage des managers {start_idx + 1} à {end_idx} sur {total_managers}")
            
            # Configuration des colonnes avec couleurs selon le statut
            def color_status(val):
                if val == "Actif":
                    return "background-color: #d4edda; color: #155724"
                elif val == "Inactif":
                    return "background-color: #f8d7da; color: #721c24"
                else:
                    return "background-color: #fff3cd; color: #856404"
            
            styled_df = paginated_df.style.applymap(color_status, subset=['Statut'])
            st.dataframe(styled_df, use_container_width=True, height=400)

# Onglet Ajouter
if "➕ Ajouter" in available_tabs:
    tab_index = available_tabs.index("➕ Ajouter")
    with tabs[tab_index]:
        st.subheader("Ajouter un Manager")
        with st.form("add_manager_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Nom complet *", placeholder="Ex: Jean Dupont")
                email = st.text_input("Email *", placeholder="jean.dupont@fixtop.com")
                nin = st.text_input("NIN", placeholder="Numéro d'identification (optionnel)")
            with col2:
                # Limiter les options de rôle uniquement à "manager"
                role_options_add = ["manager"]
                selected_role = st.selectbox("Rôle *", role_options_add)
                password = st.text_input("Mot de passe *", type="password", placeholder="Mot de passe sécurisé")
                confirm_password = st.text_input("Confirmer le mot de passe *", type="password", placeholder="Confirmez le mot de passe")
            
            submitted = st.form_submit_button("Créer le manager")
            if submitted:
                if not name.strip() or not email.strip() or not password or not confirm_password:
                    st.error("❌ Tous les champs marqués d'une * sont obligatoires")
                elif not is_valid_email(email):
                    st.error("❌ Format d'email invalide")
                elif password != confirm_password:
                    st.error("❌ Les mots de passe ne correspondent pas")
                elif len(password) < 6:
                    st.error("❌ Le mot de passe doit contenir au moins 6 caractères")
                else:
                    # Validation de la force du mot de passe
                    is_strong, errors = db_manager.validate_password_strength(password)
                    if not is_strong:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        # Récupérer role_id à partir de role_name
                        role_id = next((role['id'] for role in roles if role['name'] == selected_role), None)
                        if not role_id:
                            st.error("❌ Rôle invalide")
                        else:
                            created_by = st.session_state.get('user_id', 1)  # ID de l'utilisateur connecté
                            # Utiliser create_user au lieu de add_user
                            success, message, _ = db_manager.create_user(
                                name=name.strip(),
                                email=email.strip().lower(),
                                password=password,
                                role_id=role_id,
                                nin=nin.strip() if nin.strip() else None,
                                created_by=created_by
                            )
                            if success:
                                st.success(f"✅ {message}")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")

# Onglet Modifier
if "✏️ Modifier" in available_tabs:
    tab_index = available_tabs.index("✏️ Modifier")
    with tabs[tab_index]:
        st.subheader("Modifier un Manager")
        managers_df = load_managers_data()
        
        # Filtrer les données selon les permissions (même logique que l'onglet Liste)
        if PermissionManager.get_user_role() == 'manager' and not PermissionManager.has_permission('manager_page', 'can_view_all'):
            # Si l'utilisateur ne peut pas voir tous les managers, filtrer pour ses propres données
            user_id = PermissionManager.get_user_id()
            if user_id and not managers_df.empty:
                managers_df = managers_df[managers_df['id'] == user_id]
        
        if not managers_df.empty:
            manager_options = managers_df.apply(lambda x: f"{x['name']} ({x['email']}) - ID={x['id']}", axis=1).tolist()
            
            # Si un seul manager (le sien), sélection automatique
            if len(manager_options) == 1:
                st.info(f"📝 Modification de votre profil : {manager_options[0]}")
                selected_option = manager_options[0]
            else:
                selected_option = st.selectbox("Choisir un manager", manager_options)
            
            selected_manager_id = int(selected_option.split("ID=")[-1])
            
            # Vérifier si l'utilisateur a le droit de modifier ce manager spécifique
            current_user_id = PermissionManager.get_user_id()
            current_user_role = PermissionManager.get_user_role()
            
            # Si l'utilisateur est un manager et n'a pas la permission de tout voir,
            # il ne peut modifier que ses propres informations
            if (current_user_role == 'manager' and 
                not PermissionManager.has_permission('manager_page', 'can_view_all') and 
                selected_manager_id != current_user_id):
                st.error("❌ Vous n'avez pas les permissions pour modifier ce manager.")
                st.info("💡 Vous ne pouvez modifier que vos propres informations.")
                st.stop()
            
            manager_data = managers_df[managers_df['id'] == selected_manager_id].iloc[0]
            
            # Afficher les informations actuelles
            with st.expander("📋 Informations actuelles", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Nom :** {manager_data['name']}")
                    st.write(f"**Email :** {manager_data['email']}")
                    st.write(f"**NIN :** {manager_data.get('nin', 'Non renseigné')}")
                with col2:
                    st.write(f"**Rôle :** {manager_data.get('role_name', 'Non défini')}")
                    status_text = "Actif" if manager_data['is_active'] == 1 else "Inactif"
                    st.write(f"**Statut :** {status_text}")
                    st.write(f"**Créé le :** {manager_data.get('created_at', 'Non disponible')}")
            
            with st.form(f"edit_manager_form_{selected_manager_id}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Nom complet *", value=manager_data['name'] or "")
                    new_email = st.text_input("Email *", value=manager_data['email'] or "")
                    new_nin = st.text_input("NIN", value=manager_data['nin'] or "")
                with col2:
                    # Limiter les options de rôle uniquement à "manager"
                    role_options_edit = ["manager"]
                    current_role_index = 0  # Toujours 0 car il n'y a qu'une option
                    new_role = st.selectbox("Rôle *", role_options_edit, index=current_role_index)
                    new_status = st.selectbox("Statut", ["Actif", "Inactif"], index=0 if manager_data['is_active'] == 1 else 1)
                    change_password = st.checkbox("Changer le mot de passe")
                    new_password = st.text_input("Nouveau mot de passe", type="password", placeholder="Nouveau mot de passe sécurisé" if change_password else "Cochez 'Changer le mot de passe' pour activer", disabled=not change_password)
                    confirm_new_password = st.text_input("Confirmer le nouveau mot de passe", type="password", placeholder="Confirmez le nouveau mot de passe" if change_password else "Cochez 'Changer le mot de passe' pour activer", disabled=not change_password)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    update_submitted = st.form_submit_button("💾 Mettre à jour", type="primary")
                with col2:
                    if st.form_submit_button("🔄 Réinitialiser"):
                        st.rerun()
                with col3:
                    if manager_data['is_active'] == 1:
                        deactivate_submitted = st.form_submit_button("🔒 Désactiver", type="secondary")
                    else:
                        activate_submitted = st.form_submit_button("✅ Activer", type="secondary")
                
                if update_submitted:
                    if not new_name.strip() or not new_email.strip():
                        st.error("❌ Le nom et l'email sont obligatoires")
                    elif not is_valid_email(new_email):
                        st.error("❌ Format d'email invalide")
                    elif change_password and (not new_password or len(new_password) < 6):
                        st.error("❌ Le mot de passe doit contenir au moins 6 caractères")
                    elif change_password and new_password != confirm_new_password:
                        st.error("❌ Les mots de passe ne correspondent pas")
                    else:
                        # Validation de la force du mot de passe si changé
                        validation_passed = True
                        if change_password and new_password:
                            is_strong, errors = db_manager.validate_password_strength(new_password)
                            if not is_strong:
                                for error in errors:
                                    st.error(f"❌ {error}")
                                validation_passed = False
                        
                        if validation_passed:
                            # Récupérer role_id à partir de new_role
                            new_role_id = next((role['id'] for role in roles if role['name'] == new_role), None)
                            if not new_role_id:
                                st.error("❌ Rôle invalide")
                            else:
                                updated_by = st.session_state.get('user_id', 1)
                                # Appel corrigé à update_user avec paramètres nommés
                                success, message = db_manager.update_user(
                                    user_id=selected_manager_id,
                                    name=new_name.strip(),
                                    email=new_email.strip().lower(),
                                    role_id=new_role_id,
                                    nin=new_nin.strip() if new_nin.strip() else None,
                                    is_active=1 if new_status == "Actif" else 0,
                                    updated_by=updated_by
                                )
                                
                                # Mise à jour du mot de passe séparément si nécessaire
                                if success and change_password and new_password:
                                    hashed_password = db_manager.hash_password(new_password)
                                    with db_manager.get_connection() as conn:
                                        conn.execute("UPDATE user SET password = ? WHERE id = ?", (hashed_password, selected_manager_id))
                                        conn.commit()
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                
                # Traitement de la désactivation/activation
                if 'deactivate_submitted' in locals() and deactivate_submitted:
                    success, message = db_manager.update_user(selected_manager_id, is_active=0, updated_by=st.session_state.get('user_id', 1))
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                
                if 'activate_submitted' in locals() and activate_submitted:
                    success, message = db_manager.update_user(selected_manager_id, is_active=1, updated_by=st.session_state.get('user_id', 1))
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        else:
            st.error("❌ Impossible de récupérer les données des managers")

# Onglet Statistiques
if "📊 Statistiques" in available_tabs:
    tab_index = available_tabs.index("📊 Statistiques")
    with tabs[tab_index]:
        st.subheader("Statistiques des Managers")
        try:
            stats = db_manager.get_user_stats()
            # Filtrer pour les managers si nécessaire
            manager_stats = {k: v for k, v in stats.items() if k != 'by_role'}
            manager_by_role = [r for r in stats['by_role'] if r['name'] == 'manager']
            manager_stats['by_role'] = manager_by_role if manager_by_role else [{'name': 'manager', 'count': 0}]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Managers", manager_stats['total'])
            with col2:
                st.metric("Actifs", manager_stats['active'])
            with col3:
                st.metric("Inactifs", manager_stats['inactive'])
            
            if manager_stats['by_role']:
                df_stats = pd.DataFrame(manager_stats['by_role'])
                st.subheader("Managers par Rôle")
                st.dataframe(df_stats)
        except Exception as e:
            st.error(f"Erreur lors du chargement des statistiques : {str(e)}")
            st.info("Fonctionnalité de statistiques à implémenter")