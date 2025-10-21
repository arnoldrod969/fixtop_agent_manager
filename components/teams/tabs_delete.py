import streamlit as st
from services.teams.data_loader import load_teams_data
import time
from database import db_manager
from services.cache_utils import clear_cache

def display():
    st.subheader("🗑️ Delete Team")
    st.warning("⚠️ **Attention:** Team deletion is irreversible!")

    teams_df = load_teams_data()

    if not teams_df.empty:
        # Team selection section
        st.subheader("🎯 Select Team to Delete")

        team_options = teams_df.apply(lambda x: f"{x['name']} - ID={x['id']}", axis=1).tolist()
        selected_option = st.selectbox(
            "Choose a team to delete",
            [""] + team_options,
            help="Select the team you want to delete"
        )

        if selected_option:
            selected_team_id = int(selected_option.split("ID=")[-1])
            team_data = teams_df[teams_df['id'] == selected_team_id].iloc[0]

            # Get detailed team information
            current_team = db_manager.get_team_by_id(selected_team_id)
            members = db_manager.get_team_members(selected_team_id)

            # Display team information
            with st.expander("📋 Team Information", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Name:** {team_data['name']}")
                    st.write(f"**Description:** {team_data.get('description', 'No description')}")
                    st.write(f"**Code:** {current_team.get('code', 'N/A') if current_team else 'N/A'}")
                with col2:
                    manager_name = current_team.get('manager_name',
                                                    'No manager assigned') if current_team else 'No manager assigned'
                    st.write(f"**Manager:** {manager_name}")
                    st.write(f"**Number of members:** {len(members)}")
                    st.write(f"**Created on:** {team_data.get('created_at', 'Not available')}")

            # Members validation
            if members:
                st.error("❌ **Cannot delete this team**")
                st.write(
                    "This team still contains members. You must first remove all members before you can delete the team.")

                # Show current members
                st.subheader("👥 Current Members")
                for member in members:
                    st.write(f"• **{member['user_name']}** ({member['user_role']}) - {member['user_email']}")

                st.info("💡 **Tip:** Use the 'Edit' tab to remove members from this team before deleting it.")

            else:
                # Team can be deleted
                st.success("✅ **This team can be deleted**")
                st.write("This team contains no members and can be safely deleted.")

                # Confirmation section
                st.subheader("⚠️ Deletion Confirmation")

                confirmation_text = st.text_input(
                    f"Type the team name '{team_data['name']}' to confirm:",
                    placeholder=f"Type '{team_data['name']}' here"
                )

                name_confirmed = confirmation_text.strip() == team_data['name']

                if not name_confirmed and confirmation_text.strip():
                    st.error("❌ Name does not match")

                # Final confirmation checkbox
                final_confirmation = st.checkbox(
                    f"I confirm I want to delete the team '{team_data['name']}'",
                    key="final_delete_confirmation"
                )

                # Delete button
                if name_confirmed and final_confirmation:
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("🗑️ Delete Team", type="primary", key="execute_delete_btn"):
                            success, message = db_manager.delete_team(
                                selected_team_id,
                                st.session_state.get('user_id', 1)
                            )

                            if success:
                                st.success(f"✅ {message}")
                                st.balloons()
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")

                    with col2:
                        if st.button("❌ Cancel", key="cancel_delete_btn"):
                            st.session_state.final_delete_confirmation = False
                            st.rerun()

                elif not name_confirmed:
                    st.info("ℹ️ Please confirm the team name to continue")
                elif not final_confirmation:
                    st.info("ℹ️ Please check the confirmation box to continue")

    else:
        st.info("No teams available for deletion.")
