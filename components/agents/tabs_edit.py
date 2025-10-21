import streamlit as st
import time
from database import db_manager
from permissions import PermissionManager
from services.agents.data_loader import load_agents_data , is_valid_email , load_roles_data

roles = load_roles_data()

def display():
    st.subheader("Edit an Agent")
    agents_df = load_agents_data()
    if not agents_df.empty:
        # Filter agents according to permissions
        current_user_role = PermissionManager.get_user_role()
        current_user_id = PermissionManager.get_user_id()

        # If the user is an agent, they can only edit their own information
        if current_user_role == 'agent' and not PermissionManager.has_permission('agent_page', 'can_view_all'):
            if current_user_id:
                agents_df = agents_df[agents_df['id'] == current_user_id]
            else:
                st.error("❌ Unable to identify your user profile.")
                st.stop()

        if agents_df.empty:
            st.warning("No agents available for editing.")
            st.stop()

        # Create options for the selectbox
        agent_options = agents_df.apply(lambda x: f"{x['name']} ({x['email']}) - ID={x['id']}", axis=1).tolist()

        # If only one agent (case of agent editing their own info), display an informative message
        if len(agent_options) == 1:
            st.info(f"📝 Editing your profile: {agent_options[0]}")
            selected_option = agent_options[0]
        else:
            selected_option = st.selectbox("Choose an agent", agent_options)

        selected_agent_id = int(selected_option.split("ID=")[-1])

        # Additional permission check for editing
        if not PermissionManager.can_edit_user(selected_agent_id, 'agent'):
            st.error("❌ You do not have permissions to edit this agent.")
            st.info("💡 You can only edit your own information.")
            st.stop()

        agent_data = agents_df[agents_df['id'] == selected_agent_id].iloc[0]

        # Display current information
        with st.expander("📋 Current information", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Name:** {agent_data['name']}")
                st.write(f"**Email:** {agent_data['email']}")
                st.write(f"**NIN:** {agent_data.get('nin', 'Not provided')}")
            with col2:
                st.write(f"**Role:** {agent_data.get('role_name', 'Not defined')}")
                status_text = "Active" if agent_data['is_active'] == 1 else "Inactive"
                st.write(f"**Status:** {status_text}")
                st.write(f"**Created on:** {agent_data.get('created_at', 'Not available')}")

        with st.form(f"edit_agent_form_{selected_agent_id}"):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Full name *", value=agent_data['name'] or "")
                new_email = st.text_input("Email *", value=agent_data['email'] or "")
                new_nin = st.text_input("NIN", value=agent_data['nin'] or "")
            with col2:
                # Limit role options to "agent" only
                role_options_edit = ["agent"]
                current_role_index = 0  # Always 0 since there's only one option
                new_role = st.selectbox("Role *", role_options_edit, index=current_role_index)
                new_status = st.selectbox("Status", ["Active", "Inactive"],
                                          index=0 if agent_data['is_active'] == 1 else 1)
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
                if agent_data['is_active'] == 1:
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
                                user_id=selected_agent_id,
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
                                                 (hashed_password, selected_agent_id))
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
                success, message = db_manager.update_user(selected_agent_id, is_active=0,
                                                          updated_by=st.session_state.get('user_id', 1))
                if success:
                    st.success(f"✅ {message}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

            if 'activate_submitted' in locals() and activate_submitted:
                success, message = db_manager.update_user(selected_agent_id, is_active=1,
                                                          updated_by=st.session_state.get('user_id', 1))
                if success:
                    st.success(f"✅ {message}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    else:
        st.error("❌ Unable to retrieve agent data")
