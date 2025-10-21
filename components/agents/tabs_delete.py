import streamlit as st

from database import db_manager
from services.agents.data_loader import load_agents_data


def display():
    st.header("🗑️ Delete an agent")
    st.warning("⚠️ **Warning:** Deleting an agent is irreversible!")

    # Load agent data
    agents_df = load_agents_data()

    if agents_df.empty:
        st.info("No agents available for deletion.")
    else:
        # Agent selector
        st.subheader("🎯 Select the agent to delete")

        # Create a list of options with name and email
        agent_options = {}
        for _, agent in agents_df.iterrows():
            display_name = f"{agent['name']} ({agent['email']}) - ID: {agent['id']}"
            agent_options[display_name] = agent['id']

        selected_agent_display = st.selectbox(
            "Choose an agent to delete",
            [""] + list(agent_options.keys()),
            help="Select the agent you want to delete"
        )

        if selected_agent_display:
            selected_agent_id = agent_options[selected_agent_display]

            # Retrieve complete data of the selected agent
            try:
                agent_data = db_manager.get_user_by_id(selected_agent_id)

                if agent_data:
                    # Display information of the agent to be deleted
                    st.error(f"🎯 **Agent selected for deletion:** {agent_data['name']}")

                    with st.expander("📋 Agent information", expanded=True):
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

                    # Deletion confirmation
                    st.subheader("⚠️ Deletion confirmation")

                    confirmation_text = st.text_input(
                        f"To confirm deletion, type the agent's name: **{agent_data['name']}**",
                        placeholder=f"Type exactly: {agent_data['name']}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("🗑️ Confirm deletion", type="primary",
                                     disabled=(confirmation_text != agent_data['name'])):
                            try:
                                success, message = db_manager.delete_user(selected_agent_id)

                                if success:
                                    st.success(f"✅ {message}")
                                    st.balloons()
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")

                            except Exception as e:
                                st.error(f"❌ Unexpected error: {str(e)}")

                    with col2:
                        if st.button("❌ Cancel"):
                            st.rerun()

                    if confirmation_text != agent_data['name'] and confirmation_text:
                        st.error("The entered name does not match. Please type exactly the agent's name.")
                else:
                    st.error("Agent not found in database.")

            except Exception as e:
                st.error(f"Error retrieving agent data: {str(e)}")
