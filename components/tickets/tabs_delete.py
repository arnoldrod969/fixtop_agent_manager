import streamlit as st
from services.data_loader import load_tickets
from database import db_manager
from services.cache_utils import clear_cache

def display():
    st.header("Delete a Ticket")
    st.warning(
        "⚠️ Warning: This action will mark the ticket as inactive (logical deletion)."
    )

    tickets = load_tickets()

    if tickets:
        # Ticket selection for deletion
        ticket_options = {
            f"#{t['id']} - {t['customer_name']} ({t['customer_phone']})": t["id"]
            for t in tickets
        }

        selected_ticket_key = st.selectbox(
            "Select a ticket to delete",
            options=list(ticket_options.keys()),
            key="delete_ticket_select",
        )

        if selected_ticket_key:
            ticket_id = ticket_options[selected_ticket_key]
            ticket = db_manager.get_problem_by_id(ticket_id)

            if ticket:
                # Display ticket details
                st.markdown("### Details of the ticket to delete:")

                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**ID:** {ticket['id']}")
                    st.write(f"**Customer:** {ticket['customer_name']}")
                    st.write(f"**Phone:** {ticket['customer_phone']}")

                with col2:
                    st.write(
                        f"**Created by:** {ticket['created_by_name'] or 'Unknown'}"
                    )
                    st.write(f"**Date:** {ticket['created_at']}")

                st.write(f"**Problem:** {ticket['problem_desc']}")

                # Deletion confirmation
                col1, col2, col3 = st.columns([1, 1, 2])

                with col1:
                    if st.button(
                        "🗑️ Confirm Deletion", type="primary", key="confirm_delete"
                    ):
                        success, message = db_manager.delete_problem(ticket_id)

                        if success:
                            st.success(f"✅ {message}")
                            clear_cache()
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")

                with col2:
                    if st.button("❌ Cancel", key="cancel_delete"):
                        st.rerun()
    else:
        st.info("No tickets available for deletion.")
