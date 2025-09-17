import streamlit as st
from database import DatabaseManager

def login_page():
    """Page de connexion"""
    st.set_page_config(
        page_title="Fixtop Agent Manager - Login",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed"  # Masque la sidebar
    )
    
    # CSS pour masquer complètement la sidebar et le bouton de toggle
    st.markdown("""
        <style>
        .css-1d391kg {display: none}
        .css-1rs6os {display: none}
        .css-17ziqus {display: none}
        [data-testid="stSidebar"] {display: none}
        [data-testid="collapsedControl"] {display: none}
        .css-1lcbmhc {display: none}
        .css-1outpf7 {display: none}
        </style>
    """, unsafe_allow_html=True)
    
    # Interface de login centrée
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 🔐 Login")
        st.markdown("### Fixtop Agent Manager")
        
        with st.form("login_form"):
            username = st.text_input("Login", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 4, 1])

            with col_btn2:
                login_button = st.form_submit_button("Sign in", use_container_width=True, type="primary")
            
            if login_button:
                # Validation simple (vous pouvez la remplacer par une vraie authentification)
                if username and password:
                    # Authentification admin en dur (conservée)
                    if username == "admin@admin.com" and password == "admin":  # Exemple de validation
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_role = "admin"  # Rôle admin
                        st.success("Connexion réussie!")
                        st.rerun()
                    else:
                        # Authentification via base de données
                        try:
                            db_manager = DatabaseManager()
                            user_data = db_manager.authenticate_user(username, password)
                            
                            if user_data:
                                st.session_state.logged_in = True
                                st.session_state.username = username
                                st.session_state.user_id = user_data['id']
                                st.session_state.user_name = user_data['name']
                                st.session_state.user_role = user_data['role_name']
                                st.success(f"Connexion réussie! Bienvenue {user_data['name']}")
                                st.rerun()
                            else:
                                st.error("Email ou mot de passe incorrect")
                        except Exception as e:
                            st.error(f"Erreur de connexion : {str(e)}")
                else:
                    st.error("Veuillez remplir tous les champs")

def home_page():
    """Page d'accueil après connexion"""
    # Sidebar avec informations utilisateur
    with st.sidebar:
        st.title("🤖 Fixtop Agent")
        
        # Affichage des informations utilisateur selon le type de connexion
        if hasattr(st.session_state, 'user_name'):
            # Utilisateur de la base de données
            st.markdown(f"**Connecté en tant que:** {st.session_state.user_name}")
            st.markdown(f"**Email:** {st.session_state.username}")
            st.markdown(f"**Rôle:** {st.session_state.user_role}")
        else:
            # Admin en dur
            st.markdown(f"**Connecté en tant que:** {st.session_state.username}")
            st.markdown(f"**Rôle:** Administrateur")
        
        st.markdown("---")
        
        if st.button("🚪 Déconnexion"):
            # Nettoyer toutes les variables de session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Contenu principal de la page d'accueil
    st.title("🏠 Tableau de Bord - Fixtop Agent Manager")
    
    # Métriques générales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🤖 Agents Actifs", "12", "↗️ +2")
    
    with col2:
        st.metric("👥 Utilisateurs", "45", "↗️ +5")
    
    with col3:
        st.metric("📋 Tâches", "128", "↘️ -3")
    
    with col4:
        st.metric("⚡ Performance", "94%", "↗️ +1%")
    
    # Graphiques et informations
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Activité Récente")
        st.info("Graphique d'activité à implémenter")
    
    with col2:
        st.subheader("🔔 Notifications")
        st.warning("3 agents nécessitent une attention")
        st.info("Mise à jour système disponible")
        st.success("Sauvegarde automatique effectuée")

def main():
    """Fonction principale"""
    st.set_page_config(
        page_title="Fixtop Agent Manager",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialisation des variables de session
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # Affichage conditionnel
    if st.session_state.logged_in:
        home_page()
    else:
        login_page()

if __name__ == '__main__':
    main()

