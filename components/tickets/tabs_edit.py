import streamlit as st
from database import db_manager
from services.data_loader import load_tickets
from services.cache_utils import clear_cache

def display():
    st.header("Edit a Ticket")

    tickets = load_tickets()

    if tickets:
        # Select ticket to edit
        ticket_options = {
            f"#{t['id']} - {t['customer_name']} ({t['customer_phone']})": t["id"]
            for t in tickets
        }

        selected_ticket_key = st.selectbox(
            "Select a ticket to edit",
            options=list(ticket_options.keys()),
            key="modify_ticket_select",
        )

        if selected_ticket_key:
            ticket_id = ticket_options[selected_ticket_key]
            ticket = db_manager.get_problem_by_id(ticket_id)

            if ticket:
                with st.form("modify_ticket_form"):
                    col1, col2 = st.columns(2)

                    with col1:
                        new_customer_name = st.text_input(
                            "Customer Name",
                            value=ticket["customer_name"],
                            key="modify_customer_name",
                        )
                        new_customer_phone = st.text_input(
                            "Customer Phone",
                            value=ticket["customer_phone"],
                            key="modify_customer_phone",
                        )

                    with col2:
                        st.info(
                            f"**Created by:** {ticket['created_by_name'] or 'Unknown'}"
                        )
                        st.info(f"**Creation date:** {ticket['created_at']}")

                    new_problem_desc = st.text_area(
                        "Problem Description",
                        value=ticket["problem_desc"],
                        height=150,
                        key="modify_problem_desc",
                    )

                    submitted = st.form_submit_button("💾 Update", type="primary")

                    if submitted:
                        if (
                            not new_customer_name
                            or not new_customer_phone
                            or not new_problem_desc
                        ):
                            st.error("⚠️ All fields are required.")
                        else:
                            # Update ticket
                            success, message = db_manager.update_problem(
                                problem_id=ticket_id,
                                customer_name=new_customer_name.strip(),
                                customer_phone=new_customer_phone.strip(),
                                problem_desc=new_problem_desc.strip(),
                                updated_by=st.session_state.user_id,
                            )

                            if success:
                                st.success(f"✅ {message}")
                                clear_cache()
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
    else:
        st.info("No tickets available for editing.")
