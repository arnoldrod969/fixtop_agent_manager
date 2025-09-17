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
if not PermissionManager.check_page_access('agent_page'):
    PermissionManager.show_access_denied("Vous n'avez pas les permissions nécessaires pour accéder à cette page.")

"""Page de gestion des agents"""
st.title("🤖 Gestion des Agents")

# Définir les fonctions de chargement des données
def load_agents_data():
    """Charge les données des agents depuis la base de données"""
    try:
        # Récupérer tous les utilisateurs avec le rôle "agent"
        users = db_manager.get_all_users()
        if users:
            df = pd.DataFrame(users)
            # Filtrer uniquement les agents
            agents_df = df[df['role_name'] == 'agent'].copy()
            # Convertir les dates
            if 'created_at' in agents_df.columns:
                agents_df['created_at'] = pd.to_datetime(agents_df['created_at'])
            if 'updated_at' in agents_df.columns:
                agents_df['updated_at'] = pd.to_datetime(agents_df['updated_at'])
            return agents_df
        else:
            # Retourner un DataFrame vide avec les colonnes attendues
            return pd.DataFrame(columns=['id', 'nin', 'name', 'email', 'role_name', 'is_active', 'created_at'])
    except Exception as e:
        st.error(f"Erreur lors du chargement des agents : {str(e)}")
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
available_tabs = PermissionManager.get_available_tabs('agent_page')

if not available_tabs:
    st.error("Aucun onglet disponible pour votre rôle.")
    st.stop()

# Créer les onglets dynamiquement
tabs = st.tabs(available_tabs)

# Charger les rôles globalement pour les réutiliser
roles = load_roles_data()

# Onglet Consulter (équivalent à Liste)
if "📋 Liste" in available_tabs:
    tab_index = available_tabs.index("📋 Liste")
    with tabs[tab_index]:
        st.subheader("📋 Liste des Agents")
        
        # Charger les données
        agents_df = load_agents_data()
        
        if not agents_df.empty:
            # Dans l'onglet Liste, tous les utilisateurs peuvent voir tous les agents (consultation uniquement)
            # Le filtrage par permissions s'applique uniquement à l'onglet Modifier
            
            
            # Filtres
            col1, col2 = st.columns(2)
            
            with col1:
                status_filter = st.selectbox(
                    "Filtrer par statut",
                    ["Tous", "Actifs", "Inactifs"]
                )
            
            with col2:
                search_term = st.text_input("Rechercher par nom ou email", placeholder="Tapez pour rechercher...")
            
            # Appliquer les filtres
            filtered_df = agents_df.copy()
            
            if status_filter == "Actifs":
                filtered_df = filtered_df[filtered_df['is_active'] == 1]
            elif status_filter == "Inactifs":
                filtered_df = filtered_df[filtered_df['is_active'] == 0]
            
            if search_term.strip():
                search_lower = search_term.lower()
                filtered_df = filtered_df[
                    filtered_df['name'].str.lower().str.contains(search_lower, na=False) |
                    filtered_df['email'].str.lower().str.contains(search_lower, na=False)
                ]
            
            # Préparer l'affichage
            display_df = filtered_df.copy()
            if not display_df.empty:
                display_df['Statut'] = display_df['is_active'].apply(lambda x: "Actif" if x == 1 else "Inactif")
                display_df = display_df[['id', 'nin', 'name', 'email', 'role_name', 'Statut', 'created_at']]
                display_df.columns = ['ID', 'NIN', 'Nom', 'Email', 'Rôle', 'Statut', 'Date création']
                display_df = display_df.reset_index(drop=True)
            
            # Pagination simple
            if not display_df.empty:
                st.dataframe(display_df, use_container_width=True, height=400)

# Onglet Ajouter
if "➕ Ajouter" in available_tabs:
    tab_index = available_tabs.index("➕ Ajouter")
    with tabs[tab_index]:
        st.subheader("Ajouter un Agent")
        with st.form("add_agent_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Nom complet *", placeholder="Ex: Jean Dupont")
                email = st.text_input("Email *", placeholder="jean.dupont@fixtop.com")
                nin = st.text_input("NIN", placeholder="Numéro d'identification (optionnel)")
            with col2:
                # Limiter les options de rôle à "agent" uniquement
                role_options_add = ["agent"]
                selected_role = st.selectbox("Rôle *", role_options_add)
                password = st.text_input("Mot de passe *", type="password", placeholder="Mot de passe sécurisé")
                confirm_password = st.text_input("Confirmer le mot de passe *", type="password", placeholder="Confirmez le mot de passe")
            
            submitted = st.form_submit_button("Créer l'agent")
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
                            # Appel corrigé à create_user avec role_id au lieu de role_name
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
        st.subheader("Modifier un Agent")
        agents_df = load_agents_data()
        if not agents_df.empty:
            # Filtrer les agents selon les permissions
            current_user_role = PermissionManager.get_user_role()
            current_user_id = PermissionManager.get_user_id()
            
            # Si l'utilisateur est un agent, il ne peut modifier que ses propres informations
            if current_user_role == 'agent' and not PermissionManager.has_permission('agent_page', 'can_view_all'):
                if current_user_id:
                    agents_df = agents_df[agents_df['id'] == current_user_id]
                else:
                    st.error("❌ Impossible d'identifier votre profil utilisateur.")
                    st.stop()
            
            if agents_df.empty:
                st.warning("Aucun agent disponible pour modification.")
                st.stop()
            
            # Créer les options pour le selectbox
            agent_options = agents_df.apply(lambda x: f"{x['name']} ({x['email']}) - ID={x['id']}", axis=1).tolist()
            
            # Si un seul agent (cas de l'agent qui modifie ses propres infos), afficher un message informatif
            if len(agent_options) == 1:
                st.info(f"📝 Modification de votre profil : {agent_options[0]}")
                selected_option = agent_options[0]
            else:
                selected_option = st.selectbox("Choisir un agent", agent_options)
            
            selected_agent_id = int(selected_option.split("ID=")[-1])
            
            # Vérification supplémentaire des permissions pour la modification
            if not PermissionManager.can_edit_user(selected_agent_id, 'agent'):
                st.error("❌ Vous n'avez pas les permissions pour modifier cet agent.")
                st.info("💡 Vous ne pouvez modifier que vos propres informations.")
                st.stop()
            
            agent_data = agents_df[agents_df['id'] == selected_agent_id].iloc[0]
            
            # Afficher les informations actuelles
            with st.expander("📋 Informations actuelles", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Nom :** {agent_data['name']}")
                    st.write(f"**Email :** {agent_data['email']}")
                    st.write(f"**NIN :** {agent_data.get('nin', 'Non renseigné')}")
                with col2:
                    st.write(f"**Rôle :** {agent_data.get('role_name', 'Non défini')}")
                    status_text = "Actif" if agent_data['is_active'] == 1 else "Inactif"
                    st.write(f"**Statut :** {status_text}")
                    st.write(f"**Créé le :** {agent_data.get('created_at', 'Non disponible')}")
            
            with st.form(f"edit_agent_form_{selected_agent_id}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Nom complet *", value=agent_data['name'] or "")
                    new_email = st.text_input("Email *", value=agent_data['email'] or "")
                    new_nin = st.text_input("NIN", value=agent_data['nin'] or "")
                with col2:
                    # Limiter les options de rôle à "agent" uniquement
                    role_options_edit = ["agent"]
                    current_role_index = 0  # Toujours 0 car il n'y a qu'une option
                    new_role = st.selectbox("Rôle *", role_options_edit, index=current_role_index)
                    new_status = st.selectbox("Statut", ["Actif", "Inactif"], index=0 if agent_data['is_active'] == 1 else 1)
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
                    if agent_data['is_active'] == 1:
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
                                    user_id=selected_agent_id,
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
                                        conn.execute("UPDATE user SET password = ? WHERE id = ?", (hashed_password, selected_agent_id))
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
                    success, message = db_manager.update_user(selected_agent_id, is_active=0, updated_by=st.session_state.get('user_id', 1))
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                
                if 'activate_submitted' in locals() and activate_submitted:
                    success, message = db_manager.update_user(selected_agent_id, is_active=1, updated_by=st.session_state.get('user_id', 1))
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        else:
            st.error("❌ Impossible de récupérer les données des agents")

# Onglet Supprimer
if "🗑️ Supprimer" in available_tabs:
    tab_index = available_tabs.index("🗑️ Supprimer")
    with tabs[tab_index]:
        st.header("🗑️ Supprimer un agent")
        st.warning("⚠️ **Attention :** La suppression d'un agent est irréversible !")
        
        # Charger les données des agents
        agents_df = load_agents_data()
        
        if agents_df.empty:
            st.info("Aucun agent disponible pour suppression.")
        else:
            # Sélecteur d'agent
            st.subheader("🎯 Sélectionner l'agent à supprimer")
            
            # Créer une liste d'options avec nom et email
            agent_options = {}
            for _, agent in agents_df.iterrows():
                display_name = f"{agent['name']} ({agent['email']}) - ID: {agent['id']}"
                agent_options[display_name] = agent['id']
            
            selected_agent_display = st.selectbox(
                "Choisir un agent à supprimer",
                [""] + list(agent_options.keys()),
                help="Sélectionnez l'agent que vous souhaitez supprimer"
            )
            
            if selected_agent_display:
                selected_agent_id = agent_options[selected_agent_display]
                
                # Récupérer les données complètes de l'agent sélectionné
                try:
                    agent_data = db_manager.get_user_by_id(selected_agent_id)
                    
                    if agent_data:
                        # Afficher les informations de l'agent à supprimer
                        st.error(f"🎯 **Agent sélectionné pour suppression :** {agent_data['name']}")
                        
                        with st.expander("📋 Informations de l'agent", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Nom :** {agent_data['name']}")
                                st.write(f"**Email :** {agent_data['email']}")
                                st.write(f"**NIN :** {agent_data.get('nin', 'Non renseigné')}")
                            with col2:
                                st.write(f"**Rôle :** {agent_data.get('role_name', 'Non défini')}")
                                status_text = "Actif" if agent_data['is_active'] == 1 else "Inactif"
                                st.write(f"**Statut :** {status_text}")
                                st.write(f"**Créé le :** {agent_data.get('created_at', 'Non disponible')}")
                        
                        # Confirmation de suppression
                        st.subheader("⚠️ Confirmation de suppression")
                        
                        confirmation_text = st.text_input(
                            f"Pour confirmer la suppression, tapez le nom de l'agent : **{agent_data['name']}**",
                            placeholder=f"Tapez exactement : {agent_data['name']}"
                        )
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("🗑️ Confirmer la suppression", type="primary", disabled=(confirmation_text != agent_data['name'])):
                                try:
                                    success, message = db_manager.delete_user(selected_agent_id)
                                    
                                    if success:
                                        st.success(f"✅ {message}")
                                        st.balloons()
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                                        
                                except Exception as e:
                                    st.error(f"❌ Erreur inattendue : {str(e)}")
                        
                        with col2:
                            if st.button("❌ Annuler"):
                                st.rerun()
                        
                        if confirmation_text != agent_data['name'] and confirmation_text:
                            st.error("Le nom saisi ne correspond pas. Veuillez taper exactement le nom de l'agent.")
                    else:
                        st.error("Agent non trouvé dans la base de données.")
                        
                except Exception as e:
                    st.error(f"Erreur lors de la récupération des données de l'agent : {str(e)}")

# Onglet Statistiques
if "📊 Statistiques" in available_tabs:
    tab_index = available_tabs.index("📊 Statistiques")
    with tabs[tab_index]:
        st.subheader("Statistiques des Agents")
        try:
            stats = db_manager.get_user_stats()
            # Charger les données
            agents_df = load_agents_data()
            # Filtrer pour les agents si nécessaire
            agent_stats = {k: v for k, v in stats.items() if k != 'by_role'}
            agent_by_role = [r for r in stats['by_role'] if r['name'] == 'agent']
            agent_stats['by_role'] = agent_by_role if agent_by_role else [{'name': 'agent', 'count': 0}]
            
            # Affichage des statistiques
            colx1, colx2, colx3, colx4 = st.columns(4)
            
            with colx1:
                total_agents = len(agents_df)
                st.metric("Total Agents", total_agents)
            
            with colx2:
                active_agents = len(agents_df[agents_df['is_active'] == 1])
                st.metric("Agents Actifs", active_agents)
            
            with col3:
                inactive_agents = len(agents_df[agents_df['is_active'] == 0])
                st.metric("Agents Inactifs", inactive_agents)
            
            with colx4:
                if not agents_df.empty and 'created_at' in agents_df.columns:
                    recent_agents = len(agents_df[agents_df['created_at'] >= datetime.now() - timedelta(days=30)])
                    st.metric("Nouveaux (30j)", recent_agents)
                else:
                    st.metric("Nouveaux (30j)", 0)
            
            if agent_stats['by_role']:
                df_stats = pd.DataFrame(agent_stats['by_role'])
                st.subheader("Agents par Rôle")
                st.dataframe(df_stats)
        except Exception as e:
            st.error(f"Erreur lors du chargement des statistiques : {str(e)}")
            st.info("Fonctionnalité de statistiques à implémenter")