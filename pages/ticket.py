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

@st.cache_data(ttl=60)
def load_domains():
    """Charge tous les domaines depuis la base de données"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name FROM craft 
                WHERE is_active = 1 
                ORDER BY name
            """)
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        st.error(f"Erreur lors du chargement des domaines : {str(e)}")
        return []

@st.cache_data(ttl=60)
def load_specialties_by_domain(domain_id):
    """Charge les spécialités pour le domaine sélectionné"""
    if not domain_id:
        return []
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name FROM speciality 
                WHERE craft_id = ? AND is_active = 1 
                ORDER BY name
            """, (domain_id,))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        st.error(f"Erreur lors du chargement des spécialités : {str(e)}")
        return []

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
        
        # Charger les domaines pour le formulaire
        domains = load_domains()
        
        # Initialisation des variables de session pour le formulaire
        if 'form_customer_name' not in st.session_state:
            st.session_state.form_customer_name = ""
        if 'form_customer_phone' not in st.session_state:
            st.session_state.form_customer_phone = ""
        if 'form_problem_desc' not in st.session_state:
            st.session_state.form_problem_desc = ""
        if 'form_payment' not in st.session_state:
            st.session_state.form_payment = "Non"
        if 'form_amount' not in st.session_state:
            st.session_state.form_amount = 0
        if 'form_domain' not in st.session_state:
            st.session_state.form_domain = "Sélectionner un domaine..."
        if 'form_specialties' not in st.session_state:
            st.session_state.form_specialties = []
        if 'previous_domain_id' not in st.session_state:
            st.session_state.previous_domain_id = None
        
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input(
                "Nom du Client *", 
                value=st.session_state.form_customer_name,
                key="add_customer_name"
            )
            customer_phone = st.text_input(
                "Téléphone du Client *", 
                value=st.session_state.form_customer_phone,
                key="add_customer_phone"
            )
            
            # Champ paiement
            payment = st.selectbox(
                "Paiement *",
                options=["Non", "Oui"],
                index=0 if st.session_state.form_payment == "Non" else 1,
                key="add_payment",
                help="Le client a-t-il effectué un paiement ?"
            )
            
            # Mise à jour immédiate du montant quand paiement = "Non"
            if payment == "Non":
                st.session_state.form_amount = 0
            
            # Champ montant (conditionnel) - s'affiche immédiatement
            amount = None
            if payment == "Oui":
                amount = st.number_input(
                    "Montant (₦) *",
                    min_value=0,
                    step=1,
                    value=int(st.session_state.form_amount),
                    key="add_amount",
                    help="Montant du paiement en naira"
                )
            else:
                # Afficher le montant à 0 quand paiement = "Non"
                st.number_input(
                    "Montant (₦)",
                    value=0,
                    disabled=True,
                    help="Le montant est à 0 car aucun paiement n'a été effectué"
                )
        
        with col2:
            # Champ domaine (sélection simple)
            if domains:
                domain_options = {d['name']: d['id'] for d in domains}
                domain_list = ["Sélectionner un domaine..."] + list(domain_options.keys())
                
                try:
                    domain_index = domain_list.index(st.session_state.form_domain)
                except ValueError:
                    domain_index = 0
                
                selected_domain = st.selectbox(
                    "Domaine *",
                    options=domain_list,
                    index=domain_index,
                    key="add_domain",
                    help="Sélectionnez le domaine concerné par le problème"
                )
                selected_domain_id = domain_options.get(selected_domain) if selected_domain != "Sélectionner un domaine..." else None
                
                # Détecter si le domaine a changé pour réinitialiser les spécialités
                if 'previous_domain_id' not in st.session_state:
                    st.session_state.previous_domain_id = None
                
                if st.session_state.previous_domain_id != selected_domain_id:
                    st.session_state.form_specialties = []
                    st.session_state.previous_domain_id = selected_domain_id
                    
            else:
                st.warning("Aucun domaine disponible")
                selected_domain = None
                selected_domain_id = None
            
            # Champ spécialités (multi-sélection dépendant du domaine sélectionné)
            selected_specialties = []
            selected_specialty_ids = []
            if selected_domain_id:
                specialties = load_specialties_by_domain(selected_domain_id)
                if specialties:
                    specialty_options = {s['name']: s['id'] for s in specialties}
                    
                    # Filtrer les spécialités par défaut pour ne garder que celles qui existent pour ce domaine
                    valid_default_specialties = [spec for spec in st.session_state.form_specialties 
                                                if spec in specialty_options.keys()]
                    
                    selected_specialties = st.multiselect(
                        "Spécialités",
                        options=list(specialty_options.keys()),
                        default=valid_default_specialties,
                        key="add_specialties",
                        help="Sélectionnez les spécialités concernées"
                    )
                    selected_specialty_ids = [specialty_options[name] for name in selected_specialties]
                    
                    # Mise à jour immédiate de la session pour éviter le double-clic
                    st.session_state.form_specialties = selected_specialties
                else:
                    st.info("Aucune spécialité disponible pour ce domaine")
            else:
                st.info("Sélectionnez d'abord un domaine pour voir les spécialités")
                
            # Mise à jour immédiate du domaine sélectionné
            if selected_domain:
                st.session_state.form_domain = selected_domain
        
        problem_desc = st.text_area(
            "Description du Problème *", 
            height=150,
            value=st.session_state.form_problem_desc,
            key="add_problem_desc",
            help="Décrivez en détail le problème rencontré par le client"
        )
        
        # Boutons d'action
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            if st.button("➕ Créer le Ticket", type="primary", key="create_ticket_btn"):
                # Validation des champs obligatoires
                errors = []
                if not customer_name:
                    errors.append("Nom du client")
                if not customer_phone:
                    errors.append("Téléphone du client")
                if not problem_desc:
                    errors.append("Description du problème")
                if not selected_domain_id:
                    errors.append("Un domaine")
                if payment == "Oui" and (amount is None or amount <= 0):
                    errors.append("Montant du paiement (doit être supérieur à 0)")
                
                if errors:
                    st.error(f"⚠️ Les champs suivants sont obligatoires : {', '.join(errors)}")
                else:
                    # Création du ticket avec les nouveaux champs
                    try:
                        with db_manager.get_connection() as conn:
                            # Insérer le ticket principal
                            cursor = conn.execute("""
                                 INSERT INTO problems (customer_name, customer_phone, problem_desc, 
                                                     is_paid, amount, craft_ids, speciality_ids, created_by , updated_by)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ? , ?)
                             """, (
                                 customer_name.strip(),
                                 customer_phone.strip(),
                                 problem_desc.strip(),
                                 1 if payment == "Oui" else 0,
                                 amount if payment == "Oui" else 0,
                                 str(selected_domain_id) if selected_domain_id else None,
                                 ','.join(map(str, selected_specialty_ids)) if selected_specialty_ids else None,
                                 st.session_state.user_id,
                                 st.session_state.user_id
                             ))
                            
                            problem_id = cursor.lastrowid
                            
                            conn.commit()
                            st.success(f"✅ Ticket créé avec succès (ID: {problem_id})")
                            
                            # Réinitialiser le formulaire
                            st.session_state.form_customer_name = ""
                            st.session_state.form_customer_phone = ""
                            st.session_state.form_problem_desc = ""
                            st.session_state.form_payment = "Non"
                            st.session_state.form_amount = 0
                            st.session_state.form_domain = "Sélectionner un domaine..."
                            st.session_state.form_specialties = []
                            st.session_state.previous_domain_id = None
                            
                            clear_cache()
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la création : {str(e)}")
        
        with col_btn2:
            if st.button("🔄 Réinitialiser", key="reset_form_btn"):
                # Réinitialiser tous les champs du formulaire
                st.session_state.form_customer_name = ""
                st.session_state.form_customer_phone = ""
                st.session_state.form_problem_desc = ""
                st.session_state.form_payment = "Non"
                st.session_state.form_amount = 0
                st.session_state.form_domain = "Sélectionner un domaine..."
                st.session_state.form_specialties = []
                st.session_state.previous_domain_id = None
                st.rerun()
        
        # Mise à jour des variables de session (seulement pour les champs non gérés immédiatement)
        st.session_state.form_customer_name = customer_name
        st.session_state.form_customer_phone = customer_phone
        st.session_state.form_problem_desc = problem_desc
        st.session_state.form_payment = payment
        if amount is not None:
            st.session_state.form_amount = amount

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