import time

import streamlit as st

from database import db_manager
from services.users.data_loader import load_roles_data, is_valid_email

# Load roles globally to reuse in tabs
roles = load_roles_data()

def display():
    st.subheader("Add a User")
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full name *", placeholder="Ex: John Doe")
            email = st.text_input("Email *", placeholder="john.doe@fixtop.com")
            nin = st.text_input("NIN", placeholder="Identification number (optional)")
        with col2:
            role_options_add = [role['name'] for role in roles] if roles else []
            selected_roles = st.multiselect("Roles *", role_options_add, help="Select one or more roles")
            password = st.text_input("Password *", type="password", placeholder="Secure password")
            confirm_password = st.text_input("Confirm password *", type="password", placeholder="Confirm password")

        submitted = st.form_submit_button("Create user")
        if submitted:
            if not name.strip() or not email.strip() or not password or not confirm_password:
                st.error("❌ All fields marked with * are required")
            elif not selected_roles:
                st.error("❌ At least one role must be selected")
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
                    # Get role_ids from selected role names
                    role_ids = [role['id'] for role in roles if role['name'] in selected_roles]
                    if not role_ids:
                        st.error("❌ Invalid roles")
                    else:
                        created_by = st.session_state.get('user_id', 1)  # Connected user ID

                        # Create user with first role (for compatibility with user table)
                        success, message, user_id = db_manager.create_user(
                            nin=nin.strip() if nin.strip() else None,
                            name=name.strip(),
                            email=email.strip().lower(),
                            password=password,
                            role_id=role_ids[0],  # First role for user table
                            created_by=created_by
                        )

                        if success and user_id:
                            # Assign all selected roles in user_role table
                            roles_success, roles_message = db_manager.assign_user_roles(
                                user_id=user_id,
                                role_ids=role_ids,
                                created_by=created_by
                            )

                            if roles_success:
                                st.success(f"✅ User created successfully with {len(role_ids)} role(s)")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.warning(f"⚠️ User created but error during role assignment: {roles_message}")
                        else:
                            st.error(f"❌ {message}")

