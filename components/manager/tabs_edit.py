import time

import streamlit as st
from database import db_manager
from permissions import PermissionManager
from services.managers.data_loader import load_managers_data , load_roles_data , is_valid_email

roles = load_roles_data()

def display():
    st.subheader("Edit a Manager")
    managers_df = load_managers_data()

    # Filter data according to permissions (same logic as List tab)
    if PermissionManager.get_user_role() == 'manager' and not PermissionManager.has_permission('manager_page',
                                                                                               'can_view_all'):
        # If user cannot see all managers, filter for their own data
        user_id = PermissionManager.get_user_id()
        if user_id and not managers_df.empty:
            managers_df = managers_df[managers_df['id'] == user_id]

    if not managers_df.empty:
        manager_options = managers_df.apply(lambda x: f"{x['name']} ({x['email']}) - ID={x['id']}", axis=1).tolist()

        # If only one manager (their own), automatic selection
        if len(manager_options) == 1:
            st.info(f"📝 Editing your profile: {manager_options[0]}")
            selected_option = manager_options[0]
        else:
            selected_option = st.selectbox("Choose a manager", manager_options)

        selected_manager_id = int(selected_option.split("ID=")[-1])

        # Check if user has the right to edit this specific manager
        current_user_id = PermissionManager.get_user_id()
        current_user_role = PermissionManager.get_user_role()

        # If user is a manager and doesn't have permission to see all,
        # they can only edit their own information
        if (current_user_role == 'manager' and
                not PermissionManager.has_permission('manager_page', 'can_view_all') and
                selected_manager_id != current_user_id):
            st.error("❌ You do not have permissions to edit this manager.")
            st.info("💡 You can only edit your own information.")
            st.stop()

        manager_data = managers_df[managers_df['id'] == selected_manager_id].iloc[0]

        # Display current information
        with st.expander("📋 Current Information", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Name:** {manager_data['name']}")
                st.write(f"**Email:** {manager_data['email']}")
                st.write(f"**NIN:** {manager_data.get('nin', 'Not provided')}")
            with col2:
                st.write(f"**Role:** {manager_data.get('role_name', 'Not defined')}")
                status_text = "Active" if manager_data['is_active'] == 1 else "Inactive"
                st.write(f"**Status:** {status_text}")
                st.write(f"**Created on:** {manager_data.get('created_at', 'Not available')}")

        # Checkbox outside form to allow immediate interaction
        change_password = st.checkbox("Change password", key=f"change_password_{selected_manager_id}")

        with st.form(f"edit_manager_form_{selected_manager_id}"):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Full name *", value=manager_data['name'] or "")
                new_email = st.text_input("Email *", value=manager_data['email'] or "")
                new_nin = st.text_input("NIN", value=manager_data['nin'] or "")
            with col2:
                # Limit role options to "manager" only
                role_options_edit = ["manager"]
                current_role_index = 0  # Always 0 since there's only one option
                new_role = st.selectbox("Role *", role_options_edit, index=current_role_index)
                new_status = st.selectbox("Status", ["Active", "Inactive"],
                                          index=0 if manager_data['is_active'] == 1 else 1)
                new_password = st.text_input("New password", type="password",
                                             placeholder="New secure password" if change_password else "Check 'Change password' to activate",
                                             disabled=not change_password)
                confirm_new_password = st.text_input("Confirm new password", type="password",
                                                     placeholder="Confirm new password" if change_password else "Check 'Change password' to activate",
                                                     disabled=not change_password)

            col1, col2, col3 = st.columns(3)
            with col1:
                update_submitted = st.form_submit_button("💾 Update", type="primary")
            with col2:
                if st.form_submit_button("🔄 Reset"):
                    st.rerun()
            with col3:
                if manager_data['is_active'] == 1:
                    deactivate_submitted = st.form_submit_button("🔒 Deactivate", type="secondary")
                else:
                    activate_submitted = st.form_submit_button("✅ Activate", type="secondary")

            if update_submitted:
                if not new_name.strip() or not new_email.strip():
                    st.error("❌ Name and email are required")
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
                        # Get role_id from new_role
                        new_role_id = next((role['id'] for role in roles if role['name'] == new_role), None)
                        if not new_role_id:
                            st.error("❌ Invalid role")
                        else:
                            updated_by = st.session_state.get('user_id', 1)
                            # Corrected call to update_user with named parameters
                            success, message = db_manager.update_user(
                                user_id=selected_manager_id,
                                name=new_name.strip(),
                                email=new_email.strip().lower(),
                                role_id=new_role_id,
                                nin=new_nin.strip() if new_nin.strip() else None,
                                is_active=1 if new_status == "Active" else 0,
                                updated_by=updated_by
                            )

                            # Update password separately if necessary
                            if success and change_password and new_password:
                                hashed_password = db_manager.hash_password(new_password)
                                with db_manager.get_connection() as conn:
                                    conn.execute("UPDATE user SET password = ? WHERE id = ?",
                                                 (hashed_password, selected_manager_id))
                                    conn.commit()

                            if success:
                                st.success(f"✅ {message}")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")

        # Handle deactivation/activation
        if 'deactivate_submitted' in locals() and deactivate_submitted:
            success, message = db_manager.update_user(selected_manager_id, is_active=0,
                                                      updated_by=st.session_state.get('user_id', 1))
            if success:
                st.success(f"✅ {message}")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ {message}")

        if 'activate_submitted' in locals() and activate_submitted:
            success, message = db_manager.update_user(selected_manager_id, is_active=1,
                                                      updated_by=st.session_state.get('user_id', 1))
            if success:
                st.success(f"✅ {message}")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ {message}")

    else:
        st.info("No managers found matching your permissions.")
