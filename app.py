import streamlit as st

from components.sidebar import show_sidebar
from database import DatabaseManager, db_manager

def login_page():
    """Login page"""
    st.set_page_config(
        page_title="Fixtop Agent Manager - Login",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed"  # Hide sidebar
    )
    
    # CSS to completely hide sidebar and toggle button
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
    
    # Centered login interface
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
                # Simple validation (you can replace with real authentication)
                if username and password:
                    # Hardcoded admin authentication (kept)
                    if username == "admin@admin.com" and password == "admin":  # Example validation
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_role = "admin"  # Admin role
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        # Database authentication
                        try:
                            db_manager = DatabaseManager()
                            user_data = db_manager.authenticate_user(username, password)
                            if user_data:
                                # Get all user roles
                                user_roles = db_manager.get_user_roles(user_data['id'])
                                
                                # Store basic information in session
                                st.session_state.authenticated = True
                                st.session_state.username = username
                                st.session_state.user_id = user_data['id']
                                st.session_state.user_name = user_data['name']
                                st.session_state.user_legacy_role = user_data['role_name']  # Legacy role for compatibility
                                st.session_state.user_roles = user_roles  # All available roles
                                
                                # If user has only one role, select it automatically
                                if len(user_roles) == 1:
                                    st.session_state.logged_in = True
                                    st.session_state.user_role = user_roles[0]['name']
                                    st.session_state.selected_role_id = user_roles[0]['id']
                                    st.success(f"Login successful! Welcome {user_data['name']}")
                                    st.rerun()
                                elif len(user_roles) > 1:
                                    # Multiple roles: redirect to role selection
                                    st.session_state.role_selection_needed = True
                                    st.success(f"Authentication successful! Please select your role.")
                                    st.rerun()
                                else:
                                    # No active role found, use legacy role
                                    st.session_state.logged_in = True
                                    st.session_state.user_role = user_data['role_name']
                                    st.session_state.selected_role_id = user_data['role_id']
                                    st.warning(f"Login with legacy role: {user_data['role_name']}")
                                    st.rerun()
                            else:
                                st.error("Incorrect email or password")
                        except Exception as e:
                            st.error(f"Connection error: {str(e)}")
                else:
                    st.error("Please fill in all fields")

def role_selection_page():
    """Page de sélection de rôle après authentification"""
    st.set_page_config(
        page_title="Sélection de rôle - Fixtop Agent Manager",
        page_icon="👤",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # CSS pour masquer la sidebar
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
    
    # Interface centrée de sélection de rôle
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 👤 Role Selection")
        st.markdown(f"### Hello {st.session_state.user_name}")
        st.markdown("You have multiple roles available. Please choose which role you want to work with:")
        
        st.markdown("---")
        
        # Display available roles
        user_roles = st.session_state.get('user_roles', [])
        
        for role in user_roles:
            col_role1, col_role2 = st.columns([3, 1])
            
            with col_role1:
                st.markdown(f"**{role['name'].title()}**")
                st.caption(f"Assigned on: {role['assigned_at']}")
            
            with col_role2:
                if st.button(f"Choose", key=f"select_role_{role['id']}", type="primary"):
                    # Select this role and finalize connection
                    st.session_state.logged_in = True
                    st.session_state.user_role = role['name']
                    st.session_state.selected_role_id = role['id']
                    
                    # Clean temporary variables
                    if 'role_selection_needed' in st.session_state:
                        del st.session_state.role_selection_needed
                    if 'authenticated' in st.session_state:
                        del st.session_state.authenticated
                    
                    st.success(f"Rôle {role['name']} sélectionné ! Redirection...")
                    st.rerun()
            
            st.markdown("---")
        
        # Bouton de déconnexion
        if st.button("🚪 Sign Out", type="secondary"):
            # Nettoyer toutes les variables de session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def home_page():
    """Home page after login"""
    # Sidebar with user information
    show_sidebar()
    # Main content of home page
    st.title("🏠 Dashboard - Fixtop Agent Manager")
    
    # Time period selector
    col_filter, col_space = st.columns([2, 3])
    with col_filter:
        time_period = st.selectbox(
            "📅 Analysis Period",
            options=['all', 'today', 'last_week', 'last_month', 'this_year'],
            format_func=lambda x: {
                'all': 'All Data',
                'today': "Today",
                'last_week': 'Last Week',
                'last_month': 'Last Month',
                'this_year': 'This Year'
            }[x],
            index=0
        )
    
    # Get real statistics from database with time filtering
    try:
        stats = db_manager.get_dashboard_stats(time_period)
        notifications = db_manager.get_recent_notifications()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        # Default values in case of error
        stats = {
            'active_users': 0,
            'active_problems': 0,
            'active_teams': 0,
            'payment_rate': 0.0,
            'new_users_period': 0,
            'new_problems_period': 0,
            'time_period': time_period
        }
        notifications = [{'type': 'error', 'message': 'Database connection error', 'icon': '❌'}]
    
    # General metrics with real data
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        # Active agents don't change with time filter (always current)
        st.metric("🤖 Active Agents", stats.get('active_teams', 0))
    
    with col2:
        # Active managers don't change with time filter (always current)
        st.metric("👨‍💼 Managers", stats.get('active_managers', 0))
    
    with col3:
        # Active teams don't change with time filter (always current)
        st.metric("👥 Teams", stats.get('active_teams_count', 0))
    
    with col4:
        # Calculate users variation based on selected period
        delta_users = f"↗️ +{stats.get('new_users_period', 0)}" if stats.get('new_users_period', 0) > 0 else None
        st.metric("👤 Users", stats.get('active_users', 0), delta_users)
    
    with col5:
        # Calculate tasks/problems variation based on selected period
        delta_problems = f"↗️ +{stats.get('new_problems_period', 0)}" if stats.get('new_problems_period', 0) > 0 else None
        st.metric("📋 Tickets", stats.get('active_problems', 0), delta_problems)
    
    with col6:
        # Payment rate as performance metric
        payment_rate = stats.get('payment_rate', 0.0)
        delta_performance = "↗️ Good" if payment_rate > 50 else "↘️ Needs improvement"
        st.metric("⚡ Payment Rate", f"{payment_rate}%", delta_performance)
    
    # Charts and information
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Recent Activity")
        
        # Display additional statistics
        if stats.get('new_users_week', 0) > 0 or stats.get('new_problems_week', 0) > 0:
            st.write("**This week:**")
            if stats.get('new_users_week', 0) > 0:
                st.write(f"• {stats['new_users_week']} new user(s)")
            if stats.get('new_problems_week', 0) > 0:
                st.write(f"• {stats['new_problems_week']} new problem(s)")
        else:
            st.info("No new activity this week")
    
    with col2:
        st.subheader("🔔 Notifications")
        
        # Display real notifications from database
        for notification in notifications:
            if notification['type'] == 'warning':
                st.warning(f"{notification['icon']} {notification['message']}")
            elif notification['type'] == 'info':
                st.info(f"{notification['icon']} {notification['message']}")
            elif notification['type'] == 'success':
                st.success(f"{notification['icon']} {notification['message']}")
            elif notification['type'] == 'error':
                st.error(f"{notification['icon']} {notification['message']}")
            else:
                st.write(f"{notification['icon']} {notification['message']}")

def main():
    """Main function"""
    st.set_page_config(
        page_title="Fixtop Agent Manager",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session variables
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # Check if user needs to select a role
    if st.session_state.get('role_selection_needed', False):
        role_selection_page()
    # Check if user is logged in
    elif st.session_state.logged_in:
        home_page()
    else:
        login_page()

if __name__ == '__main__':
    main()

