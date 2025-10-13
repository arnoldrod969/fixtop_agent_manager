import streamlit as st
import pandas as pd
from services.data_loader import load_tickets
from services.cache_utils import clear_cache

def display():
    st.header("Ticket List")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        search_customer = st.text_input(
            "🔍 Search by customer name", key="search_customer"
        )

    with col2:
        search_phone = st.text_input("📱 Search by phone", key="search_phone")

    with col3:
        if st.button("🔄 Refresh", key="refresh_list"):
            clear_cache()
            st.rerun()

    # Data loading
    tickets = load_tickets()

    if tickets:
        # Data filtering
        filtered_tickets = tickets

        if search_customer:
            filtered_tickets = [
                t
                for t in filtered_tickets
                if search_customer.lower() in t["customer_name"].lower()
            ]

        if search_phone:
            filtered_tickets = [
                t for t in filtered_tickets if search_phone in t["customer_phone"]
            ]

        # Results display
        st.info(f"📊 {len(filtered_tickets)} ticket(s) found")

        # Ticket table
        if filtered_tickets:
            df = pd.DataFrame(filtered_tickets)

            # Select columns to display
            display_columns = [
                "id",
                "customer_name",
                "customer_phone",
                "problem_desc",
                "created_by_name",
                "created_at",
            ]

            # Column renaming for display
            column_names = {
                "id": "ID",
                "customer_name": "Customer Name",
                "customer_phone": "Phone",
                "problem_desc": "Problem Description",
                "created_by_name": "Created by",
                "created_at": "Creation Date",
            }

            df_display = df[display_columns].rename(columns=column_names)

            # Dataframe display configuration
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Problem Description": st.column_config.TextColumn(width="large"),
                    "Creation Date": st.column_config.DatetimeColumn(
                        format="DD/MM/YYYY HH:mm"
                    ),
                },
            )
        else:
            st.warning("No tickets match the search criteria.")
    else:
        st.info("No tickets found in the database.")
