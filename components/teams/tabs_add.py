import streamlit as st
from database import db_manager
from services.teams.data_loader import get_available_managers
import time

def display():
    st.subheader("➕ Add Team")
    available_managers = get_available_managers()

    if not available_managers:
        st.warning(
            "⚠️ No available managers found. All managers are already assigned to teams or no managers exist.")
        st.info("💡 You need to create managers first or free up existing managers from their current teams.")
    else:
        with st.form("add_team_form"):
            col1, col2 = st.columns(2)

            with col1:
                # Team name with real-time validation hint
                name = st.text_input("Team Name *", placeholder="Ex: Technical Support Team")
                if name.strip():
                    # Check if name already exists
                    existing_teams = db_manager.get_teams()
                    existing_names = [team['name'].lower() for team in existing_teams]
                    if name.strip().lower() in existing_names:
                        st.error("❌ This team name already exists. Please choose a different name.")

                # Manager selection dropdown
                manager_options = {f"{manager['name']} ({manager['email']})": manager['id'] for manager in
                                   available_managers}
                selected_manager_display = st.selectbox(
                    "Manager *",
                    options=list(manager_options.keys()),
                    help="Select the manager who will be responsible for this team"
                )
                # Initialiser selected_manager_id avec une valeur par défaut
                selected_manager_id = None
                if selected_manager_display and selected_manager_display in manager_options:
                    selected_manager_id = manager_options[selected_manager_display]

                # Description (optional)
                description = st.text_area("Description",
                                           placeholder="Team description and responsibilities...")

                # Team members selection (optional)
                st.write("**Team Members (Optional)**")
                available_users = db_manager.get_all_users()
                if available_users:
                    # Filter out inactive users, the selected manager, and non-agent users
                    available_members = [
                        user for user in available_users
                        if user['is_active'] == 1
                           and (selected_manager_id is None or user['id'] != selected_manager_id)
                           and user['role_name'].lower() == 'agent'
                    ]

                    if available_members:
                        member_options = [f"{user['name']} - {user['email']} ({user['role_name']})" for user in
                                          available_members]
                        selected_members = st.multiselect(
                            "Select Team Members",
                            options=member_options,
                            help="Select users to add as team members (optional)"
                        )

                        # Get selected member IDs
                        selected_member_ids = []
                        for selected_member in selected_members:
                            for user in available_members:
                                if f"{user['name']} - {user['email']} ({user['role_name']})" == selected_member:
                                    selected_member_ids.append(user['id'])
                                    break
                    else:
                        selected_member_ids = []
                        st.info("No available users to add as members")
                else:
                    selected_member_ids = []
                    st.info("No users available")

            with col2:
                st.write("**Team Information**")
                st.info("📋 The team name must be unique")
                st.info("👤 Each manager can only manage one team")
                st.info("🔢 Team code will be generated automatically")
                st.info("👥 You can add members during team creation")

                # Show selected manager info
                if selected_manager_display:
                    selected_manager = next(m for m in available_managers if m['id'] == selected_manager_id)
                    st.write("**Selected Manager:**")
                    st.write(f"• Name: {selected_manager['name']}")
                    st.write(f"• Email: {selected_manager['email']}")

                # Show selected members info
                if 'selected_member_ids' in locals() and selected_member_ids:
                    st.write("**Selected Members:**")
                    for member_id in selected_member_ids:
                        member = next((u for u in available_members if u['id'] == member_id), None)
                        if member:
                            st.write(f"• {member['name']} ({member['role_name']})")

            submitted = st.form_submit_button("Create Team", type="primary")

            if submitted:
                # Validation
                errors = []

                if not name.strip():
                    errors.append("Team name is required")

                if not selected_manager_id:
                    errors.append("Manager selection is required")

                # Check team name uniqueness
                if name.strip():
                    existing_teams = db_manager.get_teams()
                    existing_names = [team['name'].lower() for team in existing_teams]
                    if name.strip().lower() in existing_names:
                        errors.append("Team name already exists")

                # Check manager availability (double-check)
                if selected_manager_id and not db_manager.is_manager_available(selected_manager_id):
                    errors.append("Selected manager is no longer available")

                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    # Create team with manager_id
                    created_by = st.session_state.get('user_id', 1)
                    success, message, team_id = db_manager.create_team(
                        name=name.strip(),
                        description=description.strip() if description.strip() else None,
                        manager_id=selected_manager_id,
                        created_by=created_by
                    )

                    if success:
                        st.success(f"✅ {message}")
                        # Show team code if available
                        if team_id:
                            team_info = db_manager.get_team_by_id(team_id)
                            if team_info and 'code' in team_info:
                                st.info(f"🔢 Team code: **{team_info['code']}**")

                        # Add selected members to the team
                        if selected_member_ids:
                            members_added = 0
                            members_failed = 0
                            for member_id in selected_member_ids:
                                member_success, member_message = db_manager.add_team_member(
                                    team_id,
                                    member_id,
                                    created_by
                                )
                                if member_success:
                                    members_added += 1
                                else:
                                    members_failed += 1

                            if members_added > 0:
                                st.success(f"✅ {members_added} member(s) added to the team successfully!")
                            if members_failed > 0:
                                st.warning(f"⚠️ {members_failed} member(s) could not be added to the team.")

                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
