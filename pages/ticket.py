import streamlit as st
import pandas as pd
from datetime import datetime
from database import db_manager
from permissions import PermissionManager

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")  # Redirige vers l'accueil/login si pas connecté

# Vérification des permissions d'accès à la page
if not PermissionManager.check_page_access('ticket_page'):
    PermissionManager.show_access_denied("Vous n'avez pas accès à la gestion des tickets.")

# Configuration de la page
st.set_page_config(
    page_title="Gestion des Tickets",
    page_icon="🎫",
    layout="wide"
)

# CSS personnalisé
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .ticket-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-active {
        color: #28a745;
        font-weight: bold;
    }
    .status-inactive {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Titre principal
st.title("🎫 Gestion des Tickets")
st.markdown("---")

# Fonctions utilitaires
@st.cache_data(ttl=60)
def load_tickets():
    """Charge tous les tickets depuis la base de données"""
    return db_manager.get_all_problems()

@st.cache_data(ttl=60)
def load_ticket_stats():
    """Charge les statistiques des tickets"""
    return db_manager.get_problem_stats()

def clear_cache():
    """Vide le cache pour actualiser les données"""
    st.cache_data.clear()

# Création des onglets basés sur les permissions
available_tabs = PermissionManager.get_available_tabs('ticket_page')

# Création dynamique des onglets selon les permissions
tabs = st.tabs(available_tabs)

# Initialisation des variables d'onglets
tab1 = tab2 = tab3 = tab4 = tab5 = None

# Attribution des onglets selon leur contenu
for i, tab_name in enumerate(available_tabs):
    if "Liste" in tab_name:
        tab1 = tabs[i]
    elif "Ajouter" in tab_name:
        tab2 = tabs[i]
    elif "Modifier" in tab_name:
        tab3 = tabs[i]
    elif "Supprimer" in tab_name:
        tab4 = tabs[i]
    elif "Statistiques" in tab_name:
        tab5 = tabs[i]

# ==================== ONGLET LISTE ====================
with tab1:
    st.header("Liste des Tickets")
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_customer = st.text_input("🔍 Rechercher par nom client", key="search_customer")
    
    with col2:
        search_phone = st.text_input("📱 Rechercher par téléphone", key="search_phone")
    
    with col3:
        if st.button("🔄 Actualiser", key="refresh_list"):
            clear_cache()
            st.rerun()
    
    # Chargement des données
    tickets = load_tickets()
    
    if tickets:
        # Filtrage des données
        filtered_tickets = tickets
        
        if search_customer:
            filtered_tickets = [t for t in filtered_tickets 
                              if search_customer.lower() in t['customer_name'].lower()]
        
        if search_phone:
            filtered_tickets = [t for t in filtered_tickets 
                              if search_phone in t['customer_phone']]
        
        # Affichage des résultats
        st.info(f"📊 {len(filtered_tickets)} ticket(s) trouvé(s)")
        
        # Tableau des tickets
        if filtered_tickets:
            df = pd.DataFrame(filtered_tickets)
            
            # Sélection des colonnes à afficher
            display_columns = ['id', 'customer_name', 'customer_phone', 'problem_desc', 
                             'created_by_name', 'created_at']
            
            # Renommage des colonnes pour l'affichage
            column_names = {
                'id': 'ID',
                'customer_name': 'Nom Client',
                'customer_phone': 'Téléphone',
                'problem_desc': 'Description du Problème',
                'created_by_name': 'Créé par',
                'created_at': 'Date de Création'
            }
            
            df_display = df[display_columns].rename(columns=column_names)
            
            # Configuration de l'affichage du dataframe
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Description du Problème": st.column_config.TextColumn(
                        width="large"
                    ),
                    "Date de Création": st.column_config.DatetimeColumn(
                        format="DD/MM/YYYY HH:mm"
                    )
                }
            )
        else:
            st.warning("Aucun ticket ne correspond aux critères de recherche.")
    else:
        st.info("Aucun ticket trouvé dans la base de données.")

# ==================== ONGLET AJOUTER ====================
if tab2 is not None:  # Seulement si l'utilisateur a les permissions
    with tab2:
        st.header("Ajouter un Nouveau Ticket")
        
        with st.form("add_ticket_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                customer_name = st.text_input("Nom du Client *", key="add_customer_name")
                customer_phone = st.text_input("Téléphone du Client *", key="add_customer_phone")
            
            with col2:
                st.write("")  # Espacement
            
            problem_desc = st.text_area("Description du Problème *", 
                                       height=150, 
                                       key="add_problem_desc",
                                       help="Décrivez en détail le problème rencontré par le client")
            
            submitted = st.form_submit_button("➕ Créer le Ticket", type="primary")
            
            if submitted:
                if not customer_name or not customer_phone or not problem_desc:
                    st.error("⚠️ Tous les champs marqués d'un * sont obligatoires.")
                else:
                    # Création du ticket
                    success, message = db_manager.create_problem(
                        customer_name=customer_name.strip(),
                        customer_phone=customer_phone.strip(),
                        problem_desc=problem_desc.strip(),
                        created_by=st.session_state.user_id
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        clear_cache()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

# ==================== ONGLET MODIFIER ====================
if tab3 is not None:  # Seulement si l'utilisateur a les permissions
    with tab3:
        st.header("Modifier un Ticket")
        
        tickets = load_tickets()
        
        if tickets:
            # Sélection du ticket à modifier
            ticket_options = {f"#{t['id']} - {t['customer_name']} ({t['customer_phone']})": t['id'] 
                             for t in tickets}
            
            selected_ticket_key = st.selectbox(
                "Sélectionner un ticket à modifier",
                options=list(ticket_options.keys()),
                key="modify_ticket_select"
            )
            
            if selected_ticket_key:
                ticket_id = ticket_options[selected_ticket_key]
                ticket = db_manager.get_problem_by_id(ticket_id)
                
                if ticket:
                    with st.form("modify_ticket_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_customer_name = st.text_input(
                                "Nom du Client", 
                                value=ticket['customer_name'],
                                key="modify_customer_name"
                            )
                            new_customer_phone = st.text_input(
                                "Téléphone du Client", 
                                value=ticket['customer_phone'],
                                key="modify_customer_phone"
                            )
                        
                        with col2:
                            st.info(f"**Créé par:** {ticket['created_by_name'] or 'Inconnu'}")
                            st.info(f"**Date de création:** {ticket['created_at']}")
                        
                        new_problem_desc = st.text_area(
                            "Description du Problème", 
                            value=ticket['problem_desc'],
                            height=150,
                            key="modify_problem_desc"
                        )
                        
                        submitted = st.form_submit_button("💾 Mettre à Jour", type="primary")
                        
                        if submitted:
                            if not new_customer_name or not new_customer_phone or not new_problem_desc:
                                st.error("⚠️ Tous les champs sont obligatoires.")
                            else:
                                # Mise à jour du ticket
                                success, message = db_manager.update_problem(
                                    problem_id=ticket_id,
                                    customer_name=new_customer_name.strip(),
                                    customer_phone=new_customer_phone.strip(),
                                    problem_desc=new_problem_desc.strip(),
                                    updated_by=st.session_state.user_id
                                )
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    clear_cache()
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
        else:
            st.info("Aucun ticket disponible pour modification.")

# ==================== ONGLET SUPPRIMER ====================
if tab4 is not None:  # Seulement si l'utilisateur a les permissions
    with tab4:
        st.header("Supprimer un Ticket")
        st.warning("⚠️ Attention: Cette action marquera le ticket comme inactif (suppression logique).")
        
        tickets = load_tickets()
        
        if tickets:
            # Sélection du ticket à supprimer
            ticket_options = {f"#{t['id']} - {t['customer_name']} ({t['customer_phone']})": t['id'] 
                             for t in tickets}
            
            selected_ticket_key = st.selectbox(
                "Sélectionner un ticket à supprimer",
                options=list(ticket_options.keys()),
                key="delete_ticket_select"
            )
            
            if selected_ticket_key:
                ticket_id = ticket_options[selected_ticket_key]
                ticket = db_manager.get_problem_by_id(ticket_id)
                
                if ticket:
                    # Affichage des détails du ticket
                    st.markdown("### Détails du ticket à supprimer:")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**ID:** {ticket['id']}")
                        st.write(f"**Client:** {ticket['customer_name']}")
                        st.write(f"**Téléphone:** {ticket['customer_phone']}")
                    
                    with col2:
                        st.write(f"**Créé par:** {ticket['created_by_name'] or 'Inconnu'}")
                        st.write(f"**Date:** {ticket['created_at']}")
                    
                    st.write(f"**Problème:** {ticket['problem_desc']}")
                    
                    # Confirmation de suppression
                    col1, col2, col3 = st.columns([1, 1, 2])
                    
                    with col1:
                        if st.button("🗑️ Confirmer la Suppression", type="primary", key="confirm_delete"):
                            success, message = db_manager.delete_problem(ticket_id)
                            
                            if success:
                                st.success(f"✅ {message}")
                                clear_cache()
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                    
                    with col2:
                        if st.button("❌ Annuler", key="cancel_delete"):
                            st.rerun()
        else:
            st.info("Aucun ticket disponible pour suppression.")

# ==================== ONGLET STATISTIQUES ====================
if tab5 is not None:
    with tab5:
        st.header("Statistiques des Tickets")
        
        # Chargement des statistiques
        stats = load_ticket_stats()
        
        # Métriques principales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📊 Total Tickets</h3>
                <h2>{stats['total']}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📅 Aujourd'hui</h3>
                <h2>{stats['today']}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_per_month = sum([m['count'] for m in stats['by_month']]) / max(len(stats['by_month']), 1)
            st.markdown(f"""
            <div class="metric-card">
                <h3>📈 Moyenne/Mois</h3>
                <h2>{avg_per_month:.1f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Graphique des tickets par mois
        if stats['by_month']:
            st.subheader("📈 Évolution des Tickets par Mois")
            
            df_months = pd.DataFrame(stats['by_month'])
            df_months['month'] = pd.to_datetime(df_months['month'])
            df_months = df_months.sort_values('month')
            
            st.line_chart(
                df_months.set_index('month')['count'],
                use_container_width=True
            )
            
            # Tableau détaillé
            st.subheader("📋 Détail par Mois")
            df_display = df_months.copy()
            df_display['month'] = df_display['month'].dt.strftime('%B %Y')
            df_display.columns = ['Mois', 'Nombre de Tickets']
            
            st.dataframe(
                  df_display,
                  use_container_width=True,
                  hide_index=True
              )
        else:
            st.info("Aucune donnée disponible pour les graphiques.")
        
        # Bouton d'actualisation
        if st.button("🔄 Actualiser les Statistiques", key="refresh_stats"):
            clear_cache()
            st.rerun()