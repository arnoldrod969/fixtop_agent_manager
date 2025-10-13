import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from services.data_loader import load_tickets, load_domains, load_teams, load_specialties_by_domain, load_agents
from services.export_utils import export_to_csv, export_to_pdf, export_to_excel
from services.cache_utils import clear_cache
from services.debug_logger import log_column_check, log_data_info


def display():
    st.header("Ticket Statistics")

    # Load tickets data
    tickets = load_tickets()

    if tickets:
        # Convert to DataFrame for easier manipulation
        tickets_df = pd.DataFrame(tickets)

        # Advanced Filters Section
        st.subheader("🔍 Advanced Filters")

        # Create filter columns - now 7 columns to include "created by" filter
        filter_col1, filter_col2, teamFilter_col, agent_col5, filter_col3, filter_col4, filter_col6 = (
            st.columns(7)
        )

        with teamFilter_col:
            # Team filter
            teams = load_teams()
            if teams:
                teams_names = [d["name"] for d in teams]
                teams_filter = st.multiselect(
                    "🏢 Teams",
                    options=teams_names,
                    help="Select one or more teams",
                    key="stats_team_filter",
                )
            else:
                teams_filter = []
            #
            #    teams = load_teams()
            #    if teams:
            #        team_names = [t["name"] for t in teams]
            #        team_filter = st.multiselect(
            #            "👥 Team",
            #            options=team_names,
            #            help="Select one or more teams",
            #            key="stats_team_filter",
            #        )
            #    else:
            #        team_filter = []
            #

        with filter_col1:
            search_ticket = st.text_input(
                "🔍 Search",
                placeholder="Customer name, phone, description...",
                key="stats_search_ticket",
            )

        with filter_col2:
            # Payment status filter
            payment_filter = st.selectbox(
                "💰 Payment Status",
                ["All", "Paid", "Unpaid"],
                help="Filter by payment status",
                key="stats_payment_filter",
            )

        with filter_col3:
            # Domain filter - Updated for multiselect
            domains = load_domains()
            if domains:
                domain_names = [d["name"] for d in domains]
                domain_filter = st.multiselect(
                    "🏢 Crafts",
                    options=domain_names,
                    help="Select one or more crafts",
                    key="stats_domain_filter",
                )
            else:
                domain_filter = []

        with filter_col4:
            # Specialty filter - Updated for multiselect and multiple domains
            specialty_options = []
            if domain_filter:  # Only if domains are selected
                selected_domain_ids = [
                    d["id"] for d in domains if d["name"] in domain_filter
                ]
                all_specialties = []
                for domain_id in selected_domain_ids:
                    specialties = load_specialties_by_domain(domain_id)
                    all_specialties.extend(specialties)

                # Remove duplicates while preserving order
                seen = set()
                unique_specialties = []
                for specialty in all_specialties:
                    if specialty["name"] not in seen:
                        unique_specialties.append(specialty)
                        seen.add(specialty["name"])

                specialty_options = [s["name"] for s in unique_specialties]

            specialty_filter = st.multiselect(
                "🎯 Specialty",
                options=specialty_options,
                help="Select one or more specialties (depends on selected domains)",
                key="stats_specialty_filter",
            )

        with agent_col5:
            # Created by filter (multiselect)
            agents = load_agents()
            if agents:
                agent_names = [agent['name'] for agent in agents]
                created_by_filter = st.multiselect(
                    "👤 Agents",
                    options=agent_names,
                    help="Select one or more agents",
                    key="stats_created_by_filter",
                )
            else:
                created_by_filter = []

        with filter_col6:
            # Date filter
            date_filter = st.selectbox(
                "📅 Date Filter",
                ["All", "Creation Date", "Modification Date"],
                help="Filter by date",
                key="stats_date_filter",
            )

        # Date range inputs
        start_date = None
        end_date = None
        if date_filter != "All":
            date_col1, date_col2 = st.columns(2)

            # Calculer des valeurs par défaut intelligentes
            if not tickets_df.empty:
                min_date = tickets_df['created_at'].min() if date_filter == "Creation Date" else tickets_df.get(
                    'updated_at', tickets_df['created_at']).min()
                max_date = tickets_df['created_at'].max() if date_filter == "Creation Date" else tickets_df.get(
                    'updated_at', tickets_df['created_at']).max()

                # Convert to date if datetime
                try:
                    min_date = pd.to_datetime(min_date).date()
                    max_date = pd.to_datetime(max_date).date()
                except:
                    from datetime import date, timedelta
                    min_date = date.today() - timedelta(days=30)
                    max_date = date.today()
            else:
                from datetime import date, timedelta
                min_date = date.today() - timedelta(days=30)
                max_date = date.today()

            with date_col1:
                start_date = st.date_input("From", value=min_date, key="statistics_start_date")
            with date_col2:
                end_date = st.date_input("To", value=max_date, key="statistics_end_date")

        # Apply filters to tickets data
        filtered_tickets = tickets_df.copy()
        
        # Log des informations de débogage silencieuses
        log_data_info(filtered_tickets, "Données initiales chargées")
        log_column_check("created_by", "created_by" in filtered_tickets.columns, "Filtrage par agent")
        log_column_check("craft_ids", "craft_ids" in filtered_tickets.columns, "Filtrage par domaine")
        log_column_check("speciality_ids", "speciality_ids" in filtered_tickets.columns, "Filtrage par spécialité")
        log_column_check("amount", "amount" in filtered_tickets.columns, "Calculs de montants")

        # Search filter
        if search_ticket:
            search_mask = (
                    filtered_tickets["customer_name"].str.contains(
                        search_ticket, case=False, na=False
                    )
                    | filtered_tickets["customer_phone"].str.contains(
                search_ticket, case=False, na=False
            )
                    | filtered_tickets["problem_desc"].str.contains(
                search_ticket, case=False, na=False
            )
            )
            filtered_tickets = filtered_tickets[search_mask]

        # Payment filter
        if payment_filter != "All":
            if payment_filter == "Paid":
                filtered_tickets = filtered_tickets[
                    filtered_tickets["is_paid"] == 1
                    ]
            elif payment_filter == "Unpaid":
                filtered_tickets = filtered_tickets[
                    filtered_tickets["is_paid"] == 0
                    ]

        # Team filter (multiselect)
        if teams_filter:
            selected_teams_ids = [
                d["id"] for d in teams if d["name"] in teams_filter
            ]
            if selected_teams_ids:
                # Filter tickets that match any of the selected teams
                team_mask = (
                    filtered_tickets["te_id"]
                    .astype(str)
                    .apply(
                        lambda x: (
                            any(
                                str(team_id) == str(x)
                                for team_id in selected_teams_ids
                            )
                            if pd.notna(x)
                            else False
                        )
                    )
                )
                filtered_tickets = filtered_tickets[team_mask]

        # Created by filter (multiselect) - Traité séparément du filtre d'équipe
        if created_by_filter:
            # Get agent IDs from selected agent names
            selected_agent_ids = []
            for agent_name in created_by_filter:
                agent = next(
                    (a for a in agents if a['name'] == agent_name),
                    None,
                )
                if agent:
                    selected_agent_ids.append(agent["id"])

            if selected_agent_ids:
                # Filter tickets that match any of the selected agents
                if "created_by" in filtered_tickets.columns:
                    created_by_mask = filtered_tickets["created_by"].isin(selected_agent_ids)
                    filtered_tickets = filtered_tickets[created_by_mask]

        # Domain filter (multiselect)
        if domain_filter:
            selected_domain_ids = [
                d["id"] for d in domains if d["name"] in domain_filter
            ]
            if selected_domain_ids:
                # Filter tickets that match any of the selected domains
                if "craft_ids" in filtered_tickets.columns:
                    domain_mask = (
                        filtered_tickets["craft_ids"]
                        .astype(str)
                        .apply(
                            lambda x: (
                                any(
                                    str(domain_id) == str(x)
                                    for domain_id in selected_domain_ids
                                )
                                if pd.notna(x)
                                else False
                            )
                        )
                    )
                    filtered_tickets = filtered_tickets[domain_mask]

        # Specialty filter (multiselect and dependent on domains)
        if specialty_filter and domain_filter:
            # Get specialty IDs from selected specialty names
            selected_specialty_ids = []
            selected_domain_ids = [
                d["id"] for d in domains if d["name"] in domain_filter
            ]
            for domain_id in selected_domain_ids:
                specialties = load_specialties_by_domain(domain_id)
                for specialty_name in specialty_filter:
                    specialty = next(
                        (s for s in specialties if s["name"] == specialty_name),
                        None,
                    )
                    if specialty and specialty["id"] not in selected_specialty_ids:
                        selected_specialty_ids.append(specialty["id"])

            if selected_specialty_ids:
                # Filter tickets that match any of the selected specialties
                # Check if speciality_ids column exists in the DataFrame
                if "speciality_ids" in filtered_tickets.columns:
                    specialty_mask = (
                        filtered_tickets["speciality_ids"]
                        .astype(str)
                        .apply(
                            lambda x: (
                                any(
                                    str(specialty_id) in str(x)
                                    for specialty_id in selected_specialty_ids
                                )
                                if pd.notna(x) and x != 'nan' and x != 'None'
                                else False
                            )
                        )
                    )
                    filtered_tickets = filtered_tickets[specialty_mask]

        # Created by filter (multiselect)
        if created_by_filter:
            # Get agent IDs from selected agent names
            selected_agent_ids = []
            for agent_name in created_by_filter:
                agent = next(
                    (a for a in agents if a['name'] == agent_name),
                    None,
                )
                if agent:
                    selected_agent_ids.append(agent["id"])

            if selected_agent_ids:
                # Filter tickets that match any of the selected agents
                if "created_by" in filtered_tickets.columns:
                    created_by_mask = filtered_tickets["created_by"].isin(selected_agent_ids)
                    filtered_tickets = filtered_tickets[created_by_mask]

        # Date filter
        if date_filter == "Creation Date" and start_date is not None and end_date is not None:
            filtered_tickets["created_at_dt"] = pd.to_datetime(filtered_tickets["created_at"])
            filtered_tickets = filtered_tickets[
                (filtered_tickets["created_at_dt"].dt.date >= start_date) &
                (filtered_tickets["created_at_dt"].dt.date <= end_date)
                ]
            filtered_tickets = filtered_tickets.drop("created_at_dt", axis=1)
        elif date_filter == "Modification Date" and start_date is not None and end_date is not None:
            # Check if updated_at column exists, if not use created_at
            if 'updated_at' in filtered_tickets.columns:
                filtered_tickets["updated_at_dt"] = pd.to_datetime(filtered_tickets["updated_at"])
                filtered_tickets = filtered_tickets[
                    (filtered_tickets["updated_at_dt"].dt.date >= start_date) &
                    (filtered_tickets["updated_at_dt"].dt.date <= end_date)
                    ]
                filtered_tickets = filtered_tickets.drop("updated_at_dt", axis=1)
            else:
                # Fallback to created_at if updated_at doesn't exist
                filtered_tickets["created_at_dt"] = pd.to_datetime(filtered_tickets["created_at"])
                filtered_tickets = filtered_tickets[
                    (filtered_tickets["created_at_dt"].dt.date >= start_date) &
                    (filtered_tickets["created_at_dt"].dt.date <= end_date)
                    ]
                filtered_tickets = filtered_tickets.drop("created_at_dt", axis=1)

        # Key Metrics
        st.subheader("📈 Key Metrics")

        # Calculate metrics
        total_tickets = len(filtered_tickets)
        paid_tickets = (
            len(filtered_tickets[filtered_tickets["is_paid"] == 1])
            if not filtered_tickets.empty
            else 0
        )
        # Calcul du montant total basé sur les tickets uniques (sans duplication due aux spécialités)
        # Utiliser les IDs de tickets comme identifiants uniques pour éviter les doublons
        if "amount" in filtered_tickets.columns:
            unique_ticket_amounts = filtered_tickets.drop_duplicates(subset=["id"])["amount"].fillna(0)
            total_amount = unique_ticket_amounts.sum() if not filtered_tickets.empty else 0
            avg_amount = (
                filtered_tickets[filtered_tickets["amount"] > 0]["amount"].mean()
                if not filtered_tickets.empty
                else 0
            )
        else:
            total_amount = 0
            avg_amount = 0

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📊 Total Tickets  (By craft)", total_tickets)
        with col2:
            st.metric("💰 Paid Tickets  (By craft)", paid_tickets)
        with col3:
            st.metric("💵 Total Amount (By craft)", f"₦{total_amount:,.0f}")
        with col4:
            st.metric(
                "📈 Avg Amount", f"₦{avg_amount:.0f}" if avg_amount > 0 else "₦0"
            )

        # Commission Metrics Section
        st.subheader("💰 Commission Metrics")
        
        # Commission calculation functions
        def calculate_agent_commission(amount):
            """Calculate agent commission: 3% with 1500 NAIRA cap"""
            if pd.isna(amount) or amount <= 0:
                return 0
            return min(amount * 0.03, 1500)
        
        def calculate_manager_commission(amount):
            """Calculate manager commission: 150 NAIRA if amount >= 20000"""
            if pd.isna(amount) or amount < 20000:
                return 0
            return 150

        if not filtered_tickets.empty:
            # Get unique tickets to avoid duplicates in commission calculations
            unique_tickets = filtered_tickets.drop_duplicates(subset=["id"])
            
            # Calculate agent commissions
            agent_commissions = {}
            manager_commissions = {}
            
            for _, ticket in unique_tickets.iterrows():
                amount = ticket.get("amount", 0)
                if pd.isna(amount):
                    amount = 0
                
                # Agent commission
                agent_id = ticket.get("created_by")
                agent_name = ticket.get("created_by_name", "Unknown")
                if agent_id:
                    if agent_id not in agent_commissions:
                        agent_commissions[agent_id] = {
                            "name": agent_name,
                            "team_id": ticket.get("te_id"),
                            "tickets": 0,
                            "total_amount": 0,
                            "commission": 0
                        }
                    
                    agent_commissions[agent_id]["tickets"] += 1
                    agent_commissions[agent_id]["total_amount"] += amount
                    agent_commissions[agent_id]["commission"] += calculate_agent_commission(amount)
                
                # Manager commission (based on team)
                team_id = ticket.get("te_id")
                if team_id and amount >= 20000:  # Only for eligible tickets
                    if team_id not in manager_commissions:
                        # Find team/manager name
                        team_name = "N/A"
                        if teams:
                            try:
                                team_id_int = int(team_id)
                                team = next((t for t in teams if t["id"] == team_id_int), None)
                                if team:
                                    team_name = team["name"]
                            except:
                                pass
                        
                        manager_commissions[team_id] = {
                            "name": f"Manager - {team_name}",
                            "team_name": team_name,
                            "eligible_tickets": 0,
                            "commission": 0
                        }
                    
                    manager_commissions[team_id]["eligible_tickets"] += 1
                    manager_commissions[team_id]["commission"] += calculate_manager_commission(amount)
            
            # Calculate totals
            total_agent_commission = sum(data["commission"] for data in agent_commissions.values())
            total_manager_commission = sum(data["commission"] for data in manager_commissions.values())
            total_agents = len(agent_commissions)
            total_managers = len(manager_commissions)
            
            # Display commission metrics
            comm_col1, comm_col2, comm_col3, comm_col4 = st.columns(4)
            
            with comm_col1:
                st.metric("💰 Total Agent Commission", f"₦{total_agent_commission:,.0f}")
            with comm_col2:
                st.metric("👥 Total Manager Commission", f"₦{total_manager_commission:,.0f}")
            with comm_col3:
                st.metric("📊 Agents Concerned", total_agents)
            with comm_col4:
                st.metric("🏢 Managers Concerned", total_managers)
            
            # Detailed commission tables
            if agent_commissions or manager_commissions:
                st.subheader("📊 Detailed Commission Breakdown")
                
                # Create tabs for detailed view
                if agent_commissions and manager_commissions:
                    tab1, tab2 = st.tabs(["👤 Agent Commissions", "👥 Manager Commissions"])
                elif agent_commissions:
                    tab1 = st.tabs(["👤 Agent Commissions"])[0]
                    tab2 = None
                elif manager_commissions:
                    tab2 = st.tabs(["👥 Manager Commissions"])[0]
                    tab1 = None
                else:
                    tab1 = tab2 = None
                
                # Agent commissions tab
                if agent_commissions and tab1:
                    with tab1:
                        agent_data = []
                        for agent_id, data in agent_commissions.items():
                            # Get team name
                            team_name = "N/A"
                            if data["team_id"] and teams:
                                try:
                                    team_id_int = int(data["team_id"])
                                    team = next((t for t in teams if t["id"] == team_id_int), None)
                                    if team:
                                        team_name = team["name"]
                                except:
                                    pass
                            
                            agent_data.append({
                                "Agent": data["name"],
                                "Team": team_name,
                                "Tickets": data["tickets"],
                                "Total Amount (₦)": f"₦{data['total_amount']:,.0f}",
                                "Commission (₦)": f"₦{data['commission']:,.0f}"
                            })
                        
                        if agent_data:
                            agent_df = pd.DataFrame(agent_data)
                            st.dataframe(agent_df, use_container_width=True, hide_index=True)
                
                # Manager commissions tab
                if manager_commissions and tab2:
                    with tab2:
                        manager_data = []
                        for team_id, data in manager_commissions.items():
                            manager_data.append({
                                "Manager": data["name"],
                                "Team": data["team_name"],
                                "Eligible Tickets": data["eligible_tickets"],
                                "Commission (₦)": f"₦{data['commission']:,.0f}"
                            })
                        
                        if manager_data:
                            manager_df = pd.DataFrame(manager_data)
                            st.dataframe(manager_df, use_container_width=True, hide_index=True)
        else:
            # No filtered tickets
            comm_col1, comm_col2, comm_col3, comm_col4 = st.columns(4)
            
            with comm_col1:
                st.metric("💰 Total Agent Commission", "₦0")
            with comm_col2:
                st.metric("👥 Total Manager Commission", "₦0")
            with comm_col3:
                st.metric("📊 Agents Concerned", "0")
            with comm_col4:
                st.metric("🏢 Managers Concerned", "0")

        # Enhanced data table
        st.subheader("📋 Detailed Ticket List")

        if not filtered_tickets.empty:
            # Prepare enhanced data
            enhanced_data = []
            for _, ticket in filtered_tickets.iterrows():

                # Get team name
                team_name = "N/A"
                if ticket.get("te_id"):
                    try:
                        team_id = int(ticket["te_id"])
                        team = next(
                            (d for d in teams if d["id"] == team_id), None
                        )
                        if team:
                            team_name = team["name"]
                    except:
                        pass

                # Get agent names
                agents_names = []
                if ticket.get("created_by"):
                    print("")

                # Get domain name
                domain_name = "N/A"
                if ticket.get("craft_ids"):
                    try:
                        domain_id = int(ticket["craft_ids"])
                        domain = next(
                            (d for d in domains if d["id"] == domain_id), None
                        )
                        if domain:
                            domain_name = domain["name"]
                    except:
                        pass

                # Get specialty names
                specialty_names = []
                if ticket.get("speciality_ids"):
                    try:
                        specialty_ids = ticket["speciality_ids"].split(",")
                        for spec_id in specialty_ids:
                            if spec_id.strip():
                                # Load specialties for the domain to get names
                                if ticket.get("craft_ids"):
                                    domain_id = int(ticket["craft_ids"])
                                    specialties = load_specialties_by_domain(
                                        domain_id
                                    )
                                    specialty = next(
                                        (
                                            s
                                            for s in specialties
                                            if s["id"] == int(spec_id.strip())
                                        ),
                                        None,
                                    )
                                    if specialty:
                                        specialty_names.append(specialty["name"])
                    except:
                        pass

                # Format creation date
                try:
                    created_date = pd.to_datetime(ticket["created_at"]).strftime(
                        "%d/%m/%Y %H:%M"
                    )
                except:
                    created_date = ticket["created_at"]

                # Format last modified date
                try:
                    if ticket.get("updated_at"):
                        last_modified = pd.to_datetime(
                            ticket["updated_at"]
                        ).strftime("%d/%m/%Y %H:%M")
                    else:
                        last_modified = "N/A"
                except:
                    last_modified = ticket.get("updated_at", "N/A")

                # Create a row for each specialty (or one row if no specialties)
                if specialty_names:
                    for specialty_name in specialty_names:
                        # Apply specialty filter at the row level
                        if specialty_filter:
                            # Only include this row if the specialty matches the filter
                            if specialty_name not in specialty_filter:
                                continue

                        enhanced_data.append(
                            {
                                "Ticket ID": ticket["id"],
                                "Agent": ticket.get(
                                    "created_by_name", "Unknown"
                                ),
                                "Team": team_name,
                                "Customer Name": ticket["customer_name"],
                                "Phone": ticket["customer_phone"],
                                "Problem Description": (
                                    ticket["problem_desc"][:50] + "..."
                                    if len(str(ticket["problem_desc"])) > 50
                                    else ticket["problem_desc"]
                                ),
                                "Domain": domain_name,
                                "Specialty": specialty_name,
                                "Payment Status": (
                                    "Paid" if ticket["is_paid"] == 1 else "Unpaid"
                                ),
                                "Amount (₦)": (
                                    f"₦{ticket['amount']:,.0f}"
                                    if ticket.get("amount", 0) > 0
                                    else "₦0"
                                ),
                                "Creation Date": created_date,
                                "Last Modified": last_modified,
                            }
                        )
                else:
                    # If no specialties, create one row with "N/A" only if no specialty filter is applied
                    if not specialty_filter:
                        enhanced_data.append(
                            {
                                "Ticket ID": ticket["id"],
                                "Agent": ticket.get(
                                    "created_by_name", "Unknown"
                                ),
                                "Team": team_name,
                                "Customer Name": ticket["customer_name"],
                                "Phone": ticket["customer_phone"],
                                "Problem Description": (
                                    ticket["problem_desc"][:50] + "..."
                                    if len(str(ticket["problem_desc"])) > 50
                                    else ticket["problem_desc"]
                                ),
                                "Domain": domain_name,
                                "Specialty": "N/A",
                                "Payment Status": (
                                    "Paid" if ticket["is_paid"] == 1 else "Unpaid"
                                ),
                                "Amount (₦)": (
                                    f"₦{ticket['amount']:,.0f}"
                                    if ticket.get("amount", 0) > 0
                                    else "₦0"
                                ),
                                "Creation Date": created_date,
                                "Last Modified": last_modified,
                            }
                        )

            display_df = pd.DataFrame(enhanced_data)
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Export functionality
            st.subheader("📤 Export Data")

            export_col1, export_col2, export_col3 = st.columns(3)

            # Prepare commission data for export
            commission_data = {}
            if not filtered_tickets.empty:
                # Get unique tickets for commission calculations
                unique_tickets = filtered_tickets.drop_duplicates(subset=["id"])
                
                # Recalculate commissions for export (reuse logic from above)
                agent_commissions_export = {}
                manager_commissions_export = {}
                
                for _, ticket in unique_tickets.iterrows():
                    amount = ticket.get("amount", 0)
                    if pd.isna(amount):
                        amount = 0
                    
                    # Agent commission
                    agent_id = ticket.get("created_by")
                    agent_name = ticket.get("created_by_name", "Unknown")
                    if agent_id:
                        if agent_id not in agent_commissions_export:
                            agent_commissions_export[agent_id] = {
                                "name": agent_name,
                                "team_id": ticket.get("te_id"),
                                "tickets": 0,
                                "total_amount": 0,
                                "commission": 0
                            }
                        
                        agent_commissions_export[agent_id]["tickets"] += 1
                        agent_commissions_export[agent_id]["total_amount"] += amount
                        agent_commissions_export[agent_id]["commission"] += calculate_agent_commission(amount)
                    
                    # Manager commission
                    team_id = ticket.get("te_id")
                    if team_id and amount >= 20000:
                        if team_id not in manager_commissions_export:
                            team_name = "N/A"
                            if teams:
                                try:
                                    team_id_int = int(team_id)
                                    team = next((t for t in teams if t["id"] == team_id_int), None)
                                    if team:
                                        team_name = team["name"]
                                except:
                                    pass
                            
                            manager_commissions_export[team_id] = {
                                "name": f"Manager - {team_name}",
                                "team_name": team_name,
                                "eligible_tickets": 0,
                                "commission": 0
                            }
                        
                        manager_commissions_export[team_id]["eligible_tickets"] += 1
                        manager_commissions_export[team_id]["commission"] += calculate_manager_commission(amount)
                
                # Prepare agent commission DataFrame
                if agent_commissions_export:
                    agent_export_data = []
                    for agent_id, data in agent_commissions_export.items():
                        team_name = "N/A"
                        if data["team_id"] and teams:
                            try:
                                team_id_int = int(data["team_id"])
                                team = next((t for t in teams if t["id"] == team_id_int), None)
                                if team:
                                    team_name = team["name"]
                            except:
                                pass
                        
                        agent_export_data.append({
                            "Agent": data["name"],
                            "Team": team_name,
                            "Tickets": data["tickets"],
                            "Total Amount (₦)": data["total_amount"],
                            "Commission (₦)": data["commission"]
                        })
                    commission_data["agent_commissions"] = pd.DataFrame(agent_export_data)
                
                # Prepare manager commission DataFrame
                if manager_commissions_export:
                    manager_export_data = []
                    for team_id, data in manager_commissions_export.items():
                        manager_export_data.append({
                            "Manager": data["name"],
                            "Team": data["team_name"],
                            "Eligible Tickets": data["eligible_tickets"],
                            "Commission (₦)": data["commission"]
                        })
                    commission_data["manager_commissions"] = pd.DataFrame(manager_export_data)

            with export_col1:
                csv_data = export_to_csv(display_df)
                if csv_data:
                    st.download_button(
                        label="📄 Export to CSV",
                        data=csv_data,
                        file_name=f"ticket_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        help="Download the filtered data as CSV file",
                    )

            with export_col2:
                if st.button("📄 Export to PDF", key="prepare_pdf_button"):
                    # Create comprehensive data for PDF export
                    pdf_data_dict = {"tickets": display_df}
                    if commission_data:
                        pdf_data_dict.update(commission_data)
                    
                    pdf_data = export_to_pdf(pdf_data_dict, "Ticket Statistics & Commission Report")
                    if pdf_data:
                        st.download_button(
                            label="📄 Export to PDF",
                            data=pdf_data,
                            file_name=f"ticket_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            help="Download the filtered data as PDF file",
                        )

            with export_col3:
                # Create comprehensive data for Excel export
                excel_data_dict = {"Tickets": display_df}
                if commission_data:
                    if "agent_commissions" in commission_data:
                        excel_data_dict["Agent Commissions"] = commission_data["agent_commissions"]
                    if "manager_commissions" in commission_data:
                        excel_data_dict["Manager Commissions"] = commission_data["manager_commissions"]
                
                excel_data = export_to_excel(excel_data_dict, "Ticket Statistics & Commission Report")
                if excel_data:
                    st.download_button(
                        label="📊 Export to Excel",
                        data=excel_data,
                        file_name=f"ticket_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help="Download the filtered data as Excel file",
                    )

                # Refresh button
                if st.button("🔄 Refresh Statistics", key="refresh_stats"):
                    clear_cache()
                    st.rerun()
