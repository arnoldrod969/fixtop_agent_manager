import streamlit as st
import pandas as pd

from services.managers.data_loader import load_managers_data


def display():
    st.subheader("Manager List")

    # Load managers data
    managers_df = load_managers_data()

    # In the List tab, we display all managers for all users
    # (no permission filtering here)

    # Filters and search
    col1, col2 = st.columns(2)

    with col1:
        search_manager = st.text_input("🔍 Search", placeholder="Name, email, ID...")

    with col2:
        status_filter = st.selectbox("Filter by status", ["All", "Active", "Inactive"])

    # Filter data if necessary
    filtered_df = managers_df.copy()
    if not filtered_df.empty:
        # Filter by search (name, email, ID)
        if search_manager.strip():
            search_term = search_manager.strip().lower()
            filtered_df = filtered_df[
                filtered_df['name'].str.lower().str.contains(search_term, na=False) |
                filtered_df['email'].str.lower().str.contains(search_term, na=False) |
                filtered_df['id'].astype(str).str.contains(search_term, na=False)
                ]

        # Filter by status
        if status_filter != "All":
            if status_filter == "Active":
                filtered_df = filtered_df[filtered_df['is_active'] == 1]
            elif status_filter == "Inactive":
                filtered_df = filtered_df[filtered_df['is_active'] == 0]

        # Prepare data for display
        display_df = filtered_df.copy()
        if not display_df.empty:
            display_df['Status'] = display_df['is_active'].apply(lambda x: "Active" if x == 1 else "Inactive")
            display_df = display_df[['id', 'nin', 'name', 'email', 'role_name', 'Status', 'created_at']]
            display_df.columns = ['ID', 'NIN', 'Name', 'Email', 'Role', 'Status', 'Creation Date']
            display_df = display_df.reset_index(drop=True)  # Reset index to avoid false IDs
    else:
        display_df = pd.DataFrame(columns=['ID', 'NIN', 'Name', 'Email', 'Role', 'Status', 'Creation Date'])

    # Pagination system
    if not display_df.empty:
        total_managers = len(display_df)

        # Pagination configuration
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.info(f"📊 **{total_managers}** manager(s) found")

        with col2:
            managers_per_page = st.selectbox(
                "Managers per page",
                [10, 25, 50, 100],
                index=1,  # Default 25
                key="managers_per_page_list"
            )

        with col3:
            total_pages = max(1, (total_managers - 1) // managers_per_page + 1)
            current_page = st.number_input(
                f"Page (1-{total_pages})",
                min_value=1,
                max_value=total_pages,
                value=1,
                key="current_page_managers"
            )

        # Calculate indices for pagination
        start_idx = (current_page - 1) * managers_per_page
        end_idx = min(start_idx + managers_per_page, total_managers)

        # Display paginated data
        paginated_df = display_df.iloc[start_idx:end_idx]

        # Display pagination information
        st.caption(f"Showing managers {start_idx + 1} to {end_idx} of {total_managers}")

        # Column configuration with colors according to status
        def color_status(val):
            if val == "Active":
                return "background-color: #d4edda; color: #155724"
            elif val == "Inactive":
                return "background-color: #f8d7da; color: #721c24"
            else:
                return "background-color: #fff3cd; color: #856404"

        styled_df = paginated_df.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True, height=400)
