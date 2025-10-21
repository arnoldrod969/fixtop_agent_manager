import time

import streamlit as st

from database import db_manager
from services.users.data_loader import load_users_data


def display():
    st.subheader("🗑️ Delete a User")

    # Warning about conditional deletion
    st.warning("""
            ⚠️ **Conditional Deletion:**
            - **Hard Delete** (permanent deletion) : If the user has performed no operations
            - **Soft Delete** (deactivation) : If the user has created/modified tickets, users, teams, etc.
            """)

    users_df = load_users_data()

    if not users_df.empty:
        # User selection for deletion
        user_options = {
            f"{user['name']} ({user['email']}) - ID={user['id']}": user["id"]
            for _, user in users_df.iterrows()
        }

        selected_user_key = st.selectbox(
            "Select a user to delete",
            options=list(user_options.keys()),
            key="delete_user_select",
        )

        if selected_user_key:
            selected_user_id = user_options[selected_user_key]
            user_data = users_df[users_df['id'] == selected_user_id].iloc[0]

            if not user_data.empty:
                # Check if user is a manager of an active team
                is_manager = db_manager.check_user_is_manager(selected_user_id)

                if is_manager:
                    st.error("🚫 **Cannot delete this user**")
                    st.warning("""
                            ⚠️ **Manager Protection:**
                            This user is currently managing an active team and cannot be deleted.

                            **To delete this user, you must first:**
                            1. Go to the Teams management page
                            2. Assign a different manager to their team(s) or delete their team(s)
                            3. Then return here to delete the user
                            """)
                    st.stop()

                # Check if user is a member of an active team
                is_member = db_manager.check_user_is_member(selected_user_id)

                if is_member:
                    st.error("🚫 **Cannot delete this user**")
                    st.warning("""
                            ⚠️ **Member Protection:**
                            This user is currently a member of an active team and cannot be deleted.
                            """)
                    st.stop()

                # Check what type of deletion will be performed
                has_activity = db_manager.check_user_activity(selected_user_id)
                deletion_type = "Soft Delete (Deactivation)" if has_activity else "Hard Delete (Permanent deletion)"

                # Display user details
                st.markdown("### User details to delete:")

                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**ID:** {user_data['id']}")
                    st.write(f"**Name:** {user_data['name']}")
                    st.write(f"**Email:** {user_data['email']}")
                    st.write(f"**NIN:** {user_data.get('nin', 'Not provided')}")

                with col2:
                    st.write(f"**Role:** {user_data.get('role_name', 'Not defined')}")
                    status_text = "Active" if user_data['is_active'] == 1 else "Inactive"
                    st.write(f"**Status:** {status_text}")
                    st.write(f"**Created at:** {user_data.get('created_at', 'Not available')}")

                    # Show deletion type
                    if has_activity:
                        st.error(f"**Deletion type:** {deletion_type}")
                        st.caption("⚠️ This user has activity in the system")
                    else:
                        st.success(f"**Deletion type:** {deletion_type}")
                        st.caption("✅ No activity detected - permanent deletion possible")

                # Confirmation section
                st.markdown("---")
                st.markdown("### ⚠️ Deletion confirmation")

                if has_activity:
                    st.info(
                        "🔒 The user will be **deactivated** (soft delete) because they have activity in the system.")
                else:
                    st.error(
                        "🗑️ The user will be **permanently deleted** (hard delete). This action is **irreversible**!")

                # Confirmation by typing user name
                confirmation_text = st.text_input(
                    f"To confirm deletion, type the user's name: **{user_data['name']}**",
                    placeholder=f"Type exactly: {user_data['name']}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("🗑️ Confirm deletion", type="primary",
                                 disabled=(confirmation_text != user_data['name'])):
                        try:
                            success, message, deletion_type_result = db_manager.delete_user_conditional(
                                selected_user_id)

                            if success:
                                if deletion_type_result == "hard":
                                    st.success(f"✅ {message} (Permanent deletion)")
                                    st.balloons()
                                else:
                                    st.success(f"✅ {message} (Deactivation)")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")

                        except Exception as e:
                            st.error(f"❌ Unexpected error: {str(e)}")

                with col2:
                    if st.button("❌ Cancel"):
                        st.rerun()

                # Show warning if confirmation text doesn't match
                if confirmation_text != user_data['name'] and confirmation_text:
                    st.warning("⚠️ The entered name doesn't match. Please type exactly the user's name.")

    else:
        st.info("No users available for deletion.")
