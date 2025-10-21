import streamlit as st
from services.agents.data_loader import load_agents_data

def display():
    st.subheader("📋 Agent List")

    # Load data
    agents_df = load_agents_data()

    if not agents_df.empty:
        # In List tab, all users can see all agents (read-only)
        # Permission filtering applies only to Edit tab

        # Filters
        col1, col2 = st.columns(2)

        with col1:
            status_filter = st.selectbox(
                "Filter by status",
                ["All", "Active", "Inactive"]
            )

        with col2:
            search_term = st.text_input("Search by name or email", placeholder="Type to search...")

        # Apply filters
        filtered_df = agents_df.copy()

        if status_filter == "Active":
            filtered_df = filtered_df[filtered_df['is_active'] == 1]
        elif status_filter == "Inactive":
            filtered_df = filtered_df[filtered_df['is_active'] == 0]

        if search_term.strip():
            search_lower = search_term.lower()
            filtered_df = filtered_df[
                filtered_df['name'].str.lower().str.contains(search_lower, na=False) |
                filtered_df['email'].str.lower().str.contains(search_lower, na=False)
                ]

        # Prepare display DataFrame
        display_df = filtered_df.copy()
        if not display_df.empty:
            display_df['Status'] = display_df['is_active'].apply(lambda x: "Active" if x == 1 else "Inactive")
            display_df = display_df[['id', 'nin', 'name', 'email', 'role_name', 'Status', 'created_at']]
            display_df.columns = ['ID', 'NIN', 'Name', 'Email', 'Role', 'Status', 'Creation Date']
            display_df = display_df.reset_index(drop=True)

        # Display data
        if not display_df.empty:
            st.dataframe(display_df, use_container_width=True, height=400)
        else:
            st.info("No agents found with the selected filters.")
    else:
        st.info("No agents available.")
