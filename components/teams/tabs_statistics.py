import streamlit as st
import pandas as pd
from datetime import datetime
from services.teams.data_loader import load_teams_data
from services.teams.export_utils import export_to_csv, export_to_pdf, export_to_excel
from database import db_manager
import plotly.express as px


def display():
    st.subheader("📊 Team Statistics")

    # Load teams data
    teams_df = load_teams_data()

    if not teams_df.empty:
        # Filters Section
        st.subheader("🔍 Filters")

        # Create filter columns
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

        with filter_col1:
            search_team = st.text_input("🔍 Search Team", placeholder="Team name or ID...",
                                        key="stats_search_team")

        with filter_col2:
            # Get all active managers from database (not just those assigned to teams)
            try:
                all_users = db_manager.get_all_users()
                all_managers = []
                if all_users:
                    # Filter for active managers
                    active_managers = [user for user in all_users if
                                       user['role_name'] == 'manager' and user['is_active'] == 1]
                    all_managers = [manager['name'] for manager in active_managers]
                unique_managers = sorted(list(set(all_managers)))
                selected_managers = st.multiselect(
                    "👤 Filter by Manager(s)",
                    options=unique_managers,
                    help="Select one or more managers to filter teams",
                    key="statistics_manager_filter"
                )
            except Exception as e:
                st.error(f"Error loading managers: {str(e)}")
                selected_managers = []

        with filter_col3:
            # Get all active agents from database (not just those assigned to teams)
            try:
                all_users = db_manager.get_all_users()
                all_agents = []
                if all_users:
                    # Filter for active agents
                    active_agents = [user for user in all_users if
                                     user['role_name'] == 'agent' and user['is_active'] == 1]
                    all_agents = [agent['name'] for agent in active_agents]
                unique_agents = sorted(list(set(all_agents)))
                selected_agents = st.multiselect(
                    "🧑‍💼 Filter by Agent(s)",
                    options=unique_agents,
                    help="Select one or more agents to filter teams",
                    key="statistics_agent_filter"
                )
            except Exception as e:
                st.error(f"Error loading agents: {str(e)}")
                selected_agents = []

        with filter_col4:
            # Date filters
            date_filter_type = st.selectbox("📅 Date Filter", ["All", "Creation Date", "Modification Date"],
                                            key="statistics_date_filter")

        # Date range inputs
        start_date = None
        end_date = None
        if date_filter_type != "All":
            date_col1, date_col2 = st.columns(2)

            # Calculate intelligent default values
            if not teams_df.empty:
                min_date = teams_df['created_at'].min().date() if date_filter_type == "Creation Date" else \
                    teams_df['updated_at'].min().date() if 'updated_at' in teams_df.columns else teams_df[
                        'created_at'].min().date()
                max_date = teams_df['created_at'].max().date() if date_filter_type == "Creation Date" else \
                    teams_df['updated_at'].max().date() if 'updated_at' in teams_df.columns else teams_df[
                        'created_at'].max().date()
            else:
                from datetime import date, timedelta
                min_date = date.today() - timedelta(days=30)
                max_date = date.today()

            with date_col1:
                start_date = st.date_input("From", value=min_date, key="statistics_start_date")
            with date_col2:
                end_date = st.date_input("To", value=max_date, key="statistics_end_date")

        # Apply filters
        filtered_teams = teams_df.copy()

        # Search filter
        if search_team:
            filtered_teams = filtered_teams[
                filtered_teams['name'].str.contains(search_team, case=False, na=False) |
                filtered_teams['id'].astype(str).str.contains(search_team, case=False, na=False)
                ]

        # Manager filter
        if selected_managers:  # If managers are selected
            team_ids_with_manager = []
            for _, team in filtered_teams.iterrows():
                if team.get('manager_name') in selected_managers:
                    team_ids_with_manager.append(team['id'])
            filtered_teams = filtered_teams[filtered_teams['id'].isin(team_ids_with_manager)]

        # Agent filter
        if selected_agents:
            team_ids_with_agent = []
            for _, team in filtered_teams.iterrows():
                members = db_manager.get_team_members(team['id'])
                for member in members:
                    if member.get('user_name') in selected_agents:
                        team_ids_with_agent.append(team['id'])
                        break
            filtered_teams = filtered_teams[filtered_teams['id'].isin(team_ids_with_agent)]

        # Date filter
        if date_filter_type == "Creation Date" and start_date is not None and end_date is not None:
            filtered_teams = filtered_teams[
                (filtered_teams['created_at'].dt.date >= start_date) &
                (filtered_teams['created_at'].dt.date <= end_date)
                ]
        elif date_filter_type == "Modification Date" and start_date is not None and end_date is not None:
            if 'updated_at' in filtered_teams.columns:
                filtered_teams = filtered_teams[
                    (filtered_teams['updated_at'].dt.date >= start_date) &
                    (filtered_teams['updated_at'].dt.date <= end_date)
                    ]

        # Key Metrics
        st.subheader("📈 Key Metrics")

        # Calculate metrics
        total_teams = len(filtered_teams)
        total_members = 0
        teams_with_managers = 0
        empty_teams = 0

        for _, team in filtered_teams.iterrows():
            team_details = db_manager.get_team_by_id(team['id'])
            if team_details:
                members_count = len(team_details.get('members', []))
                total_members += members_count
                if team_details.get('manager_name'):
                    teams_with_managers += 1
                if members_count == 0:
                    empty_teams += 1

        avg_team_size = total_members / total_teams if total_teams > 0 else 0

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        total_teams = len(filtered_teams)
        total_members = sum(
            len(db_manager.get_team_members(team['id'])) for _, team in filtered_teams.iterrows())
        avg_team_size = total_members / total_teams if total_teams > 0 else 0
        teams_without_members = sum(
            1 for _, team in filtered_teams.iterrows() if len(db_manager.get_team_members(team['id'])) == 0)

        with col1:
            st.metric("📊 Total Teams", total_teams)
        with col2:
            st.metric("👥 Total Members", total_members)
        with col3:
            st.metric("📈 Avg Team Size", f"{avg_team_size:.1f}")
        with col4:
            st.metric("⚠️ Empty Teams", teams_without_members)

        # Simple data table - One row per member (similar to List tab)
        # st.subheader("📋 Detailed Team List with Members")

        enhanced_data = []
        for _, team in filtered_teams.iterrows():
            members = db_manager.get_team_members(team['id'])

            try:
                created_date = pd.to_datetime(team['created_at']).strftime('%d/%m/%Y')
            except:
                created_date = team['created_at']

            # Use manager_name directly from teams_df (already available from get_teams())
            manager_name = team.get('manager_name', 'Not assigned') or 'Not assigned'

            # Get team details to retrieve the code
            team_details = db_manager.get_team_by_id(team['id'])
            team_code = team_details.get('code', 'N/A') if team_details else 'N/A'

            # If team has no members, show one row with "No members"
            if not members:
                enhanced_data.append({
                    'Team ID': team['id'],
                    'Team Name': team['name'],
                    'Code': team_code,
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
                # Create one row per member, but filter by selected agents if any
                for member in members:
                    # If agents are selected, only show members that match the selected agents
                    if selected_agents and member.get('user_name') not in selected_agents:
                        continue

                    enhanced_data.append({
                        'Team ID': team['id'],
                        'Team Name': team['name'],
                        'Code': team_code,
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
            csv_data = export_to_csv(display_df)
            if csv_data:
                st.download_button(
                    label="📄 Export to CSV",
                    data=csv_data,
                    file_name=f"team_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Download the filtered data as CSV file"
                )

        with export_col2:
            if st.button("📄 Export to PDF", key="export_pdf_button"):
                pdf_data = export_to_pdf(display_df, "Team Statistics Report")
                if pdf_data:
                    st.download_button(
                        label="📄 Export to PDF",
                        data=pdf_data,
                        file_name=f"team_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        help="Download the filtered data as PDF file"
                    )

        with export_col3:
            excel_data = export_to_excel(display_df, "Team Statistics Report")
            if excel_data:
                st.download_button(
                    label="📊 Export to Excel",
                    data=excel_data,
                    file_name=f"team_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Download the filtered data as Excel file"
                )

        # Charts Section in expandable container
        with st.expander("📊 Charts & Analytics", expanded=False):
            if not filtered_teams.empty:
                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    # Chart 1: Teams by Manager (Bar Chart)
                    manager_data = []
                    for _, team in filtered_teams.iterrows():
                        team_details = db_manager.get_team_by_id(team['id'])
                        manager_name = team_details.get('manager_name',
                                                        'No Manager') if team_details else 'No Manager'
                        manager_data.append(manager_name)

                    if manager_data:
                        manager_counts = pd.Series(manager_data).value_counts()
                        fig_bar = px.bar(
                            x=manager_counts.index,
                            y=manager_counts.values,
                            title="Number of Teams by Manager",
                            labels={'x': 'Manager', 'y': 'Number of Teams'}
                        )
                        fig_bar.update_layout(height=400)
                        st.plotly_chart(fig_bar, use_container_width=True)

                with chart_col2:
                    # Chart 2: Agents Distribution by Team (Pie Chart)
                    team_sizes = []
                    team_names = []
                    for _, team in filtered_teams.iterrows():
                        team_details = db_manager.get_team_by_id(team['id'])
                        if team_details:
                            members_count = len(team_details.get('members', []))
                            if members_count > 0:  # Only show teams with members
                                team_sizes.append(members_count)
                                team_names.append(team['name'])

                    if team_sizes:
                        fig_pie = px.pie(
                            values=team_sizes,
                            names=team_names,
                            title="Agent Distribution by Team"
                        )
                        fig_pie.update_layout(height=400)
                        st.plotly_chart(fig_pie, use_container_width=True)

                # Chart 3: Team Evolution Over Time (Line Chart)
                st.subheader("📈 Team Evolution Over Time")

                if 'created_at' in filtered_teams.columns:
                    # Group teams by creation date
                    teams_by_date = filtered_teams.groupby(filtered_teams['created_at'].dt.date).size().cumsum()

                    fig_line = px.line(
                        x=teams_by_date.index,
                        y=teams_by_date.values,
                        title="Cumulative Number of Teams Over Time",
                        labels={'x': 'Date', 'y': 'Total Teams'}
                    )
                    fig_line.update_layout(height=400)
                    st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("📊 No data available for charts. Create teams first to view analytics.")

    else:
        st.info("📊 No teams found. Create teams first to view statistics.")
        st.write("💡 **Suggestion:** Use the '➕ Add' tab to create your first team.")