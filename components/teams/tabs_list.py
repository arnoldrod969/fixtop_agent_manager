import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from services.teams.data_loader import load_teams_data
from services.teams.export_utils import export_to_csv
from database import db_manager

def display():
    # List Tab
    st.subheader("📋 Teams List")

    # Load teams data
    teams_df = load_teams_data()

    # Advanced Filters Section (moved from List tab)
    st.subheader("🔍 Advanced Filters")

    # Create filter columns
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        search_team = st.text_input("🔍 Search", placeholder="Name, description, code...", key="stats_search")

    with filter_col2:
        # Manager filter
        all_managers = []
        if not teams_df.empty:
            for _, team in teams_df.iterrows():
                team_details = db_manager.get_team_by_id(team['id'])
                if team_details and team_details.get('manager_name'):
                    all_managers.append(team_details['manager_name'])
            all_managers = sorted(list(set(all_managers)))

        manager_filter = st.selectbox(
            "👨‍💼 Filter by Manager",
            ["All managers"] + all_managers,
            help="Filter teams by assigned manager",
            key="stats_manager_filter"
        )

    with filter_col3:
        # Member count filter
        member_count_filter = st.selectbox(
            "👥 Number of members",
            ["All", "No members (0)", "Small teams (1-5)", "Medium teams (6-15)", "Large teams (16+)"],
            help="Filter by number of members",
            key="stats_member_filter"
        )

    with filter_col4:
        # Date filter
        date_filter = st.selectbox(
            "📅 Date Filter",
            ["All dates", "Creation date", "Modification date"],
            key="stats_date_filter"
        )

    # Date range inputs
    start_date = None
    end_date = None
    if date_filter != "All dates":
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input("From date", key="stats_start_date")
        with date_col2:
            end_date = st.date_input("To date", key="stats_end_date")

    # Apply advanced filters (same logic as before)
    filtered_df = teams_df.copy()
    if not filtered_df.empty:
        # Apply search filter
        if search_team.strip():
            search_term = search_team.strip().lower()
            team_codes = {}
            for _, team in filtered_df.iterrows():
                team_details = db_manager.get_team_by_id(team['id'])
                if team_details:
                    team_codes[team['id']] = team_details.get('code', '').lower()

            filtered_df = filtered_df[
                filtered_df['name'].str.lower().str.contains(search_term, na=False) |
                filtered_df['description'].str.lower().str.contains(search_term, na=False) |
                filtered_df['id'].astype(str).str.contains(search_term, na=False) |
                filtered_df['id'].apply(lambda x: search_term in team_codes.get(x, ''))
                ]

        # Apply manager filter
        if manager_filter != "All managers":
            team_ids_with_manager = []
            for _, team in filtered_df.iterrows():
                team_details = db_manager.get_team_by_id(team['id'])
                if team_details and team_details.get('manager_name') == manager_filter:
                    team_ids_with_manager.append(team['id'])
            filtered_df = filtered_df[filtered_df['id'].isin(team_ids_with_manager)]

        # Apply member count filter
        if member_count_filter != "All":
            team_ids_by_member_count = []
            for _, team in filtered_df.iterrows():
                member_count = len(db_manager.get_team_members(team['id']))
                if member_count_filter == "No members (0)" and member_count == 0:
                    team_ids_by_member_count.append(team['id'])
                elif member_count_filter == "Small teams (1-5)" and 1 <= member_count <= 5:
                    team_ids_by_member_count.append(team['id'])
                elif member_count_filter == "Medium teams (6-15)" and 6 <= member_count <= 15:
                    team_ids_by_member_count.append(team['id'])
                elif member_count_filter == "Large teams (16+)" and member_count >= 16:
                    team_ids_by_member_count.append(team['id'])
            filtered_df = filtered_df[filtered_df['id'].isin(team_ids_by_member_count)]

        # Apply date filter
        if date_filter == "Creation date" and start_date is not None and end_date is not None:
            filtered_df['created_at_dt'] = pd.to_datetime(filtered_df['created_at'])
            filtered_df = filtered_df[
                (filtered_df['created_at_dt'].dt.date >= start_date) &
                (filtered_df['created_at_dt'].dt.date <= end_date)
                ]
            filtered_df = filtered_df.drop('created_at_dt', axis=1)
        elif date_filter == "Modification date" and start_date is not None and end_date is not None:
            if 'updated_at' in filtered_df.columns:
                filtered_df['updated_at_dt'] = pd.to_datetime(filtered_df['updated_at'])
                filtered_df = filtered_df[
                    (filtered_df['updated_at_dt'].dt.date >= start_date) &
                    (filtered_df['updated_at_dt'].dt.date <= end_date)
                    ]
                filtered_df = filtered_df.drop('updated_at_dt', axis=1)

    # Display statistics and charts
    if not filtered_df.empty:
        # Enhanced data table with metrics - One row per member
        # st.subheader("📋 Detailed Team List with Members")

        enhanced_data = []
        for _, team in filtered_df.iterrows():
            members = db_manager.get_team_members(team['id'])

            try:
                created_date = pd.to_datetime(team['created_at']).strftime('%d/%m/%Y')
            except:
                created_date = team['created_at']

            # Use manager_name directly from teams_df (already available from get_teams())
            manager_name = team.get('manager_name', 'Not assigned') or 'Not assigned'

            # If team has no members, show one row with "No members"
            if not members:
                enhanced_data.append({
                    'Team ID': team['id'],
                    'Team Name': team['name'],
                    'Code': team.get('code', 'N/A'),
                    'Description': team['description'][:50] + '...' if len(str(team['description'])) > 50 else
                    team['description'],
                    'Manager': manager_name,
                    'Member': 'No members',
                    'Member Email': '-',
                    'Member Role': '-',
                    'Creation date': created_date,
                    'Last modified': team.get('updated_at', 'N/A')
                })
            else:
                # Create one row per member
                for member in members:
                    enhanced_data.append({
                        'Team ID': team['id'],
                        'Team Name': team['name'],
                        'Code': team.get('code', 'N/A'),
                        'Description': team['description'][:50] + '...' if len(
                            str(team['description'])) > 50 else team['description'],
                        'Manager': manager_name,
                        'Member': member.get('user_name', 'Unknown'),
                        'Member Email': member.get('user_email', 'N/A'),
                        'Member Role': member.get('user_role', 'N/A'),
                        'Creation date': created_date,
                        'Last modified': team.get('updated_at', 'N/A')
                    })

        display_df = pd.DataFrame(enhanced_data)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Export functionality
        st.subheader("📤 Export Data")

        export_col1, export_col2, export_col3 = st.columns(3)

        with export_col1:
            if st.button("📊 Export to CSV", key="export_csv"):
                csv_data = export_to_csv(display_df)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_data,
                    file_name=f"teams_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                st.success("✅ CSV export ready for download!")

        with export_col2:
            if st.button("📋 Export Filtered Data", key="export_filtered"):
                st.info("📋 Filtered data export prepared")

        with export_col3:
            if st.button("📈 Export Charts", key="export_charts"):
                st.info("📈 Chart export feature coming soon")

    else:
        st.info("🔍 No teams found with the applied filters.")
        st.write("💡 **Suggestions:**")
        st.write("• Adjust your filter criteria")
        st.write("• Try a broader date range")
        st.write("• Check if teams exist in the system")
