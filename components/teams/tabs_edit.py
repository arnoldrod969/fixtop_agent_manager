import streamlit as st
from database import db_manager
from services.teams.data_loader import load_teams_data , get_available_managers
import time
import pandas as pd
from services.cache_utils import clear_cache

def display():
    st.subheader("✏️ Edit Team")
    teams_df = load_teams_data()

    if not teams_df.empty:
        # Team selection with improved UI
        st.subheader("🎯 Select Team to Edit")
        team_options = teams_df.apply(lambda x: f"{x['name']} - ID={x['id']}", axis=1).tolist()
        selected_option = st.selectbox(
            "Choose a team to edit",
            team_options,
            help="Select the team you want to modify"
        )

        try:
            selected_team_id = int(selected_option.split("ID=")[-1])
            team_data = teams_df[teams_df['id'] == selected_team_id].iloc[0]

            # Get current team details including manager
            current_team = db_manager.get_team_by_id(selected_team_id)
            current_manager_id = current_team.get('manager_id') if current_team else None
            current_manager_name = current_team.get('manager_name',
                                                    'No manager assigned') if current_team else 'No manager assigned'
        except (ValueError, IndexError) as e:
            st.error("❌ Error loading team data. Please try again.")
            st.stop()

        # Display current information
        with st.expander("📋 Current Information", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Name:** {team_data['name']}")
                st.write(f"**Description:** {team_data.get('description', 'No description')}")
                st.write(f"**Code:** {current_team.get('code', 'N/A') if current_team else 'N/A'}")
            with col2:
                st.write(f"**Current Manager:** {current_manager_name}")
                members = db_manager.get_team_members(selected_team_id)
                st.write(f"**Members:** {len(members)}")
                try:
                    created_date = pd.to_datetime(team_data.get('created_at')).strftime('%d/%m/%Y %H:%M')
                except:
                    created_date = team_data.get('created_at', 'Not available')
                st.write(f"**Created on:** {created_date}")

        # Team Information Update Form
        with st.form(f"edit_team_form_{selected_team_id}"):
            st.subheader("🔧 Update Team Information")

            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input(
                    "Team Name *",
                    value=team_data['name'] or "",
                    help="Enter a unique team name"
                )
                new_description = st.text_area(
                    "Description",
                    value=team_data['description'] or "",
                    help="Describe the team's purpose and responsibilities"
                )

            with col2:
                # Manager selection
                st.write("**Manager Assignment**")
                try:
                    available_managers = get_available_managers()
                except Exception as e:
                    st.error(f"❌ Error loading managers: {str(e)}")
                    available_managers = []

                # Add current manager to options if not in available list
                manager_options = []
                manager_ids = []

                if current_manager_id and current_manager_name != 'No manager assigned':
                    manager_options.append(f"{current_manager_name} (Current)")
                    manager_ids.append(current_manager_id)

                for manager in available_managers:
                    if manager['id'] != current_manager_id:
                        manager_options.append(f"{manager['name']} - {manager['email']}")
                        manager_ids.append(manager['id'])

                if manager_options:
                    selected_manager_index = st.selectbox(
                        "Select Manager",
                        range(len(manager_options)),
                        format_func=lambda x: manager_options[x],
                        index=0 if current_manager_id else None,
                        help="Choose a manager for this team"
                    )
                    selected_manager_id = manager_ids[
                        selected_manager_index] if selected_manager_index is not None else None
                else:
                    st.warning("⚠️ No available managers found")
                    selected_manager_id = current_manager_id

                st.info("💡 The team name must be unique")

            col1, col2 = st.columns(2)
            with col1:
                update_submitted = st.form_submit_button("💾 Update Team", type="primary")
            with col2:
                if st.form_submit_button("🔄 Reset"):
                    st.rerun()

            if update_submitted:
                # Validation
                errors = []

                if not new_name.strip():
                    errors.append("Team name is required")

                # Check team name uniqueness (only if name changed)
                if new_name.strip() and new_name.strip().lower() != team_data['name'].lower():
                    try:
                        existing_teams = db_manager.get_teams()
                        existing_names = [team['name'].lower() for team in existing_teams if
                                          team['id'] != selected_team_id]
                        if new_name.strip().lower() in existing_names:
                            errors.append("Team name already exists")
                    except Exception as e:
                        errors.append(f"Error checking team name uniqueness: {str(e)}")

                # Check manager availability (only if manager changed)
                if selected_manager_id and selected_manager_id != current_manager_id:
                    try:
                        if not db_manager.is_manager_available(selected_manager_id):
                            errors.append("Selected manager is no longer available")
                    except Exception as e:
                        errors.append(f"Error checking manager availability: {str(e)}")

                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    # Prepare update parameters
                    update_params = {}

                    # Only update fields that have changed
                    if new_name.strip() != team_data['name']:
                        update_params['name'] = new_name.strip()

                    if new_description.strip() != (team_data['description'] or ""):
                        update_params[
                            'description'] = new_description.strip() if new_description.strip() else None

                    if selected_manager_id != current_manager_id:
                        update_params['manager_id'] = selected_manager_id

                    if update_params:
                        try:
                            updated_by = st.session_state.get('user_id', 1)
                            success, message = db_manager.update_team(
                                team_id=selected_team_id,
                                updated_by=updated_by,
                                **update_params
                            )
                            if success:
                                st.success(f"✅ {message}")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        except Exception as e:
                            st.error(f"❌ Error updating team: {str(e)}")
                    else:
                        st.info("ℹ️ No changes detected")

        # Team Members Management Section
        st.divider()
        st.subheader("👥 Team Members Management")

        # Current members
        try:
            members = db_manager.get_team_members(selected_team_id)
        except Exception as e:
            st.error(f"❌ Error loading team members: {str(e)}")
            members = []

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Current Members**")
            if members:
                for member in members:
                    with st.container():
                        member_col1, member_col2 = st.columns([3, 1])
                        with member_col1:
                            st.write(f"• **{member['user_name']}** ({member['user_role']})")
                            st.caption(f"📧 {member['user_email']}")
                        with member_col2:
                            if st.button("🗑️", key=f"remove_member_{member['user_id']}", help="Remove member"):
                                try:
                                    success, message = db_manager.remove_team_member(
                                        selected_team_id,
                                        member['user_id'],
                                        st.session_state.get('user_id', 1)
                                    )
                                    if success:
                                        st.success(f"✅ {message}")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                                except Exception as e:
                                    st.error(f"❌ Error removing member: {str(e)}")
            else:
                st.info("👤 No members in this team")
                st.write("💡 **Tip:** Use the 'Add New Member' section to add team members.")

        with col2:
            st.write("**Add New Member**")
            try:
                available_users = db_manager.get_available_users_for_team(selected_team_id)
            except Exception as e:
                st.error(f"❌ Error loading available users: {str(e)}")
                available_users = []

            if available_users:
                user_options = [f"{user['name']} - {user['email']} (agent)" for user in available_users]
                selected_user_index = st.selectbox(
                    "Select Agent to Add",
                    range(len(user_options)),
                    format_func=lambda x: user_options[x],
                    key="add_member_select",
                    help="Choose an agent to add to this team"
                )

                if st.button("➕ Add Member", key="add_member_btn", type="primary"):
                    try:
                        selected_user = available_users[selected_user_index]

                        # Additional validation: check that the user is an available agent
                        if selected_user['role'].lower() != 'agent':
                            st.error(
                                f"❌ Only agents can be added as team members. Selected user has role: {selected_user['role']}")
                        elif not db_manager.is_agent_available(selected_user['id']):
                            st.error(f"❌ This agent is already a member of another active team")
                        else:
                            success, message = db_manager.add_team_member(
                                selected_team_id,
                                selected_user['id'],
                                st.session_state.get('user_id', 1)
                            )
                            if success:
                                st.success(f"✅ {message}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"❌ Error adding member: {str(e)}")
            else:
                st.info("👥 No available agents to add")
                st.write("💡 **Suggestions:**")
                st.write("• All eligible agents are already team members")
                st.write("• Create new agents first")
                st.write("• Check that agents are not already assigned to other teams")

    else:
        st.info("🔍 No teams found.")
        st.write("💡 **Suggestion:** Create teams first using the '➕ Add' tab.")
        st.write("📋 You need to have at least one team to use the editing features.")
