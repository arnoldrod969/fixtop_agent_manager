import streamlit as st
import time
from database import db_manager
from services.managers.data_loader import is_valid_email , load_roles_data

roles = load_roles_data()

def display():
    st.subheader("Add a Manager")
    with st.form("add_manager_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full name *", placeholder="Ex: John Doe")
            email = st.text_input("Email *", placeholder="john.doe@fixtop.com")
            nin = st.text_input("NIN", placeholder="Identification number (optional)")
        with col2:
            # Limit role options to "manager" only
            role_options_add = ["manager"]
            selected_role = st.selectbox("Role *", role_options_add)
            password = st.text_input("Password *", type="password", placeholder="Secure password")
            confirm_password = st.text_input("Confirm password *", type="password", placeholder="Confirm password")

        submitted = st.form_submit_button("Create manager")
        if submitted:
            if not name.strip() or not email.strip() or not password or not confirm_password:
                st.error("❌ All fields marked with * are required")
            elif not is_valid_email(email):
                st.error("❌ Invalid email format")
            elif password != confirm_password:
                st.error("❌ Passwords do not match")
            elif len(password) < 6:
                st.error("❌ Password must contain at least 6 characters")
            else:
                # Password strength validation
                is_strong, errors = db_manager.validate_password_strength(password)
                if not is_strong:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    # Get role_id from role_name
                    role_id = next((role['id'] for role in roles if role['name'] == selected_role), None)
                    if not role_id:
                        st.error("❌ Invalid role")
                    else:
                        created_by = st.session_state.get('user_id', 1)  # ID of connected user
                        # Use create_user instead of add_user
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
