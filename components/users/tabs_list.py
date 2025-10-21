import pandas as pd
import streamlit as st

from services.users.data_loader import load_users_data, load_roles_data

# Load roles globally to reuse in tabs
roles = load_roles_data()

def display():
    st.subheader("User List")

    # Load user data
    users_df = load_users_data()

    # Create role filter options dynamically
    role_options = ["All"]
    if roles:
        role_options.extend([role['name'] for role in roles])

    # Filters and search
    col1, col2, col3 = st.columns(3)

    with col1:
        search_user = st.text_input("🔍 Search", placeholder="Name, email, ID...")

    with col2:
        role_filter = st.selectbox("Filter by role", role_options)

    with col3:
        status_filter = st.selectbox("Filter by status", ["All", "Active", "Inactive"])

    # Filter data if necessary
    filtered_df = users_df.copy()
    if not filtered_df.empty:
        # Filter by search (name, email, ID)
        if search_user.strip():
            search_term = search_user.strip().lower()
            filtered_df = filtered_df[
                filtered_df['name'].str.lower().str.contains(search_term, na=False) |
                filtered_df['email'].str.lower().str.contains(search_term, na=False) |
                filtered_df['id'].astype(str).str.contains(search_term, na=False)
                ]

        # Filter by role
        if role_filter != "All":
            filtered_df = filtered_df[filtered_df['role_name'] == role_filter]

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
        total_users = len(display_df)

        # Pagination configuration
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.info(f"📊 **{total_users}** user(s) found")

        with col2:
            users_per_page = st.selectbox(
                "Users per page",
                [10, 25, 50, 100],
                index=1,  # Default 25
                key="users_per_page_list"
            )

        with col3:
            total_pages = max(1, (total_users - 1) // users_per_page + 1)
            current_page = st.number_input(
                f"Page (1-{total_pages})",
                min_value=1,
                max_value=total_pages,
                value=1,
                key="current_page_list"
            )

        # Calculate indices for pagination
        start_idx = (current_page - 1) * users_per_page
        end_idx = min(start_idx + users_per_page, total_users)

        # Display paginated data
        paginated_df = display_df.iloc[start_idx:end_idx]

        # Display pagination information
        st.caption(f"Showing users {start_idx + 1} to {end_idx} of {total_users}")

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

        # Batch actions
        st.subheader("Batch Actions")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.button("📧 Send Email")
        with col2:
            st.button("⏸️ Suspend Selection")
        with col3:
            st.button("✅ Activate Selection")
        with col4:
            st.button("📤 Export List")

