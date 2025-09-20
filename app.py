import streamlit as st
from database import DatabaseManager

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
                                st.session_state.logged_in = True
                                st.session_state.username = username
                                st.session_state.user_id = user_data['id']
                                st.session_state.user_name = user_data['name']
                                st.session_state.user_role = user_data['role_name']
                                st.success(f"Login successful! Welcome {user_data['name']}")
                                st.rerun()
                            else:
                                st.error("Incorrect email or password")
                        except Exception as e:
                            st.error(f"Connection error: {str(e)}")
                else:
                    st.error("Please fill in all fields")

def home_page():
    """Home page after login"""
    # Sidebar with user information
    with st.sidebar:
        st.title("🤖 Fixtop Agent")
        
        # Display user information according to connection type
        if hasattr(st.session_state, 'user_name'):
            # Database user
            st.markdown(f"**Logged in as:** {st.session_state.user_name}")
            st.markdown(f"**Email:** {st.session_state.username}")
            st.markdown(f"**Role:** {st.session_state.user_role}")
        else:
            # Hardcoded admin
            st.markdown(f"**Logged in as:** {st.session_state.username}")
            st.markdown(f"**Role:** Administrator")
        
        st.markdown("---")
        
        if st.button("🚪 Logout"):
            # Clean all session variables
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content of home page
    st.title("🏠 Dashboard - Fixtop Agent Manager")
    
    # General metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🤖 Active Agents", "12", "↗️ +2")
    
    with col2:
        st.metric("👥 Users", "45", "↗️ +5")
    
    with col3:
        st.metric("📋 Tasks", "128", "↘️ -3")
    
    with col4:
        st.metric("⚡ Performance", "94%", "↗️ +1%")
    
    # Charts and information
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Recent Activity")
        st.info("Activity chart to be implemented")
    
    with col2:
        st.subheader("🔔 Notifications")
        st.warning("3 agents require attention")
        st.info("System update available")
        st.success("Automatic backup completed")

def main():
    """Main function"""
    st.set_page_config(
        page_title="Fixtop Agent Manager",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session variables
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # Conditional display
    if st.session_state.logged_in:
        home_page()
    else:
        login_page()

if __name__ == '__main__':
    main()

