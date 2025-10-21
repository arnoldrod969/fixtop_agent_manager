import time

import streamlit as st

from database import db_manager
from services.users.data_loader import load_users_data, load_roles_data, is_valid_email

# Load roles globally to reuse in tabs
roles = load_roles_data()

def display():
    st.subheader("Edit a User")
    users_df = load_users_data()
    if not users_df.empty:
        user_options = users_df.apply(lambda x: f"{x['name']} ({x['email']}) - ID={x['id']}", axis=1).tolist()
        selected_option = st.selectbox("Choose a user", user_options)
        selected_user_id = int(selected_option.split("ID=")[-1])
        user_data = users_df[users_df['id'] == selected_user_id].iloc[0]

        # Récupérer les rôles actuels de l'utilisateur
        current_user_roles = db_manager.get_user_roles(selected_user_id)
        current_role_names = [role['name'] for role in current_user_roles] if current_user_roles else []

        # Display current information
        with st.expander("📋 Current information", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Name:** {user_data['name']}")
                st.write(f"**Email:** {user_data['email']}")
                st.write(f"**NIN:** {user_data.get('nin', 'Not provided')}")
            with col2:
                if current_role_names:
                    st.write(f"**Roles:** {', '.join(current_role_names)}")
                else:
                    st.write(f"**Role (legacy):** {user_data.get('role_name', 'Not defined')}")
                status_text = "Active" if user_data['is_active'] == 1 else "Inactive"
                st.write(f"**Status:** {status_text}")
                st.write(f"**Created on:** {user_data.get('created_at', 'Not available')}")

        with st.form(f"edit_user_form_{selected_user_id}"):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Full name *", value=user_data['name'] or "")
                new_email = st.text_input("Email *", value=user_data['email'] or "")
                new_nin = st.text_input("NIN", value=user_data['nin'] or "")
            with col2:
                role_options_edit = [role['name'] for role in roles] if roles else []
                # Use current roles from user_role if available, otherwise fallback to role_name
                default_roles = current_role_names if current_role_names else (
                    [user_data['role_name']] if user_data.get('role_name') else [])
                new_roles = st.multiselect("Roles *", role_options_edit, default=default_roles,
                                           help="Select one or more roles")
                new_status = st.selectbox("Status", ["Active", "Inactive"],
                                          index=0 if user_data['is_active'] == 1 else 1)
                change_password = st.checkbox("Change password")
                new_password = st.text_input("New password", type="password",
                                             placeholder="New secure password" if change_password else "Check 'Change password' to enable",
                                             disabled=not change_password)
                confirm_new_password = st.text_input("Confirm new password", type="password",
                                                     placeholder="Confirm new password" if change_password else "Check 'Change password' to enable",
                                                     disabled=not change_password)

            col1, col2, col3 = st.columns(3)
            with col1:
                update_submitted = st.form_submit_button("💾 Update", type="primary")
            with col2:
                if st.form_submit_button("🔄 Reset"):
                    st.rerun()
            with col3:
                if user_data['is_active'] == 1:
                    deactivate_submitted = st.form_submit_button("🔒 Deactivate", type="secondary")
                else:
                    activate_submitted = st.form_submit_button("✅ Activate", type="secondary")

            if update_submitted:
                if not new_name.strip() or not new_email.strip():
                    st.error("❌ Name and email are required")
                elif not new_roles:
                    st.error("❌ Au moins un rôle doit être sélectionné")
                elif not is_valid_email(new_email):
                    st.error("❌ Invalid email format")
                elif change_password and (not new_password or len(new_password) < 6):
                    st.error("❌ Password must contain at least 6 characters")
                elif change_password and new_password != confirm_new_password:
                    st.error("❌ Passwords do not match")
                else:
                    # Password strength validation if changed
                    validation_passed = True
                    if change_password and new_password:
                        is_strong, errors = db_manager.validate_password_strength(new_password)
                        if not is_strong:
                            for error in errors:
                                st.error(f"❌ {error}")
                            validation_passed = False

                    if validation_passed:
                        # Get role_ids from new_roles
                        new_role_ids = [role['id'] for role in roles if role['name'] in new_roles]
                        if not new_role_ids:
                            st.error("❌ Invalid roles")
                        else:
                            updated_by = st.session_state.get('user_id', 1)

                            # Update basic user information
                            success, message = db_manager.update_user(
                                user_id=selected_user_id,
                                name=new_name.strip(),
                                email=new_email.strip().lower(),
                                role_id=new_role_ids[0],  # First role for compatibility with user table
                                nin=new_nin.strip() if new_nin.strip() else None,
                                is_active=1 if new_status == "Active" else 0,
                                updated_by=updated_by
                            )

                            if success:
                                # Update roles in user_role
                                roles_success, roles_message = db_manager.update_user_roles(
                                    user_id=selected_user_id,
                                    new_role_ids=new_role_ids,
                                    updated_by=updated_by
                                )

                                # Update password separately if necessary
                                if change_password and new_password:
                                    hashed_password = db_manager.hash_password(new_password)
                                    with db_manager.get_connection() as conn:
                                        conn.execute("UPDATE user SET password = ? WHERE id = ?",
                                                     (hashed_password, selected_user_id))
                                        conn.commit()

                                if roles_success:
                                    st.success(f"✅ User updated successfully with {len(new_role_ids)} role(s)")
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.warning(f"⚠️ User updated but error during role update: {roles_message}")
                            else:
                                st.error(f"❌ {message}")

            # Handle deactivation/activation
            if 'deactivate_submitted' in locals() and deactivate_submitted:
                success, message = db_manager.update_user(selected_user_id, is_active=0,
                                                          updated_by=st.session_state.get('user_id', 1))
                if success:
                    st.success(f"✅ {message}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

            if 'activate_submitted' in locals() and activate_submitted:
                success, message = db_manager.update_user(selected_user_id, is_active=1,
                                                          updated_by=st.session_state.get('user_id', 1))
                if success:
                    st.success(f"✅ {message}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    else:
        st.error("❌ Unable to retrieve user data")
