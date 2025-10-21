import streamlit as st
from database import db_manager
from services.tickets.data_loader import load_editable_tickets, load_domains, load_specialties_by_domain
from services.cache_utils import clear_cache
from permissions import PermissionManager

def display():
    st.header("Edit a Ticket")

    # Vérifier les permissions d'édition
    if not PermissionManager.has_permission('ticket_page', 'can_edit'):
        PermissionManager.show_access_denied("You don't have permission to edit tickets.")
        return

    # Charger seulement les tickets que l'utilisateur peut éditer
    tickets = load_editable_tickets()

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
                # Vérifier que l'utilisateur peut bien éditer ce ticket spécifique
                current_user_id = PermissionManager.get_user_id()
                current_user_role = PermissionManager.get_user_role()
                
                # Pour les agents, vérifier qu'ils sont bien le créateur du ticket
                if current_user_role == 'agent' and ticket.get('created_by') != current_user_id:
                    st.error("❌ You can only edit tickets that you have created.")
                    return

                # Load domains for the form
                domains = load_domains()
                
                # Initialize session variables for the edit form
                if f"edit_form_payment_{ticket_id}" not in st.session_state:
                    st.session_state[f"edit_form_payment_{ticket_id}"] = "Yes" if ticket.get("is_paid", 0) == 1 else "No"
                if f"edit_form_amount_{ticket_id}" not in st.session_state:
                    st.session_state[f"edit_form_amount_{ticket_id}"] = ticket.get("amount", 0)
                if f"edit_form_domain_{ticket_id}" not in st.session_state:
                    # Find domain name from craft_ids
                    current_domain = "Select a domain..."
                    if ticket.get("craft_ids") and domains:
                        for domain in domains:
                            if str(domain["id"]) == str(ticket["craft_ids"]):
                                current_domain = domain["name"]
                                break
                    st.session_state[f"edit_form_domain_{ticket_id}"] = current_domain
                if f"edit_form_specialties_{ticket_id}" not in st.session_state:
                    # Find specialty names from speciality_ids
                    current_specialties = []
                    if ticket.get("speciality_ids"):
                        specialty_ids = ticket["speciality_ids"].split(",")
                        if ticket.get("craft_ids"):
                            specialties = load_specialties_by_domain(int(ticket["craft_ids"]))
                            for specialty in specialties:
                                if str(specialty["id"]) in specialty_ids:
                                    current_specialties.append(specialty["name"])
                    st.session_state[f"edit_form_specialties_{ticket_id}"] = current_specialties
                if f"previous_domain_id_{ticket_id}" not in st.session_state:
                    st.session_state[f"previous_domain_id_{ticket_id}"] = ticket.get("craft_ids")

                with st.form("modify_ticket_form"):
                    col1, col2 = st.columns(2)

                    with col1:
                        new_customer_name = st.text_input(
                            "Customer Name *",
                            value=ticket["customer_name"],
                            key="modify_customer_name",
                        )
                        new_customer_phone = st.text_input(
                            "Customer Phone *",
                            value=ticket["customer_phone"],
                            key="modify_customer_phone",
                        )

                        # Payment field
                        payment = st.selectbox(
                            "Payment *",
                            options=["No", "Yes"],
                            index=0 if st.session_state[f"edit_form_payment_{ticket_id}"] == "No" else 1,
                            key="modify_payment",
                            help="Has the customer made a payment?",
                        )

                        # Amount field (conditional)
                        amount = None
                        if payment == "Yes":
                            amount = st.number_input(
                                "Amount (₦) *",
                                min_value=0,
                                step=1,
                                value=int(st.session_state[f"edit_form_amount_{ticket_id}"]) if payment == "Yes" else 0,
                                key="modify_amount",
                                help="Payment amount in naira",
                            )
                        else:
                            # Display amount at 0 when payment = "No"
                            st.number_input(
                                "Amount (₦)",
                                value=0,
                                disabled=True,
                                help="Amount is 0 because no payment was made",
                            )
                            amount = 0

                    with col2:
                        # Domain field
                        if domains:
                            domain_options = {d["name"]: d["id"] for d in domains}
                            domain_list = ["Select a domain..."] + list(domain_options.keys())

                            try:
                                domain_index = domain_list.index(st.session_state[f"edit_form_domain_{ticket_id}"])
                            except ValueError:
                                domain_index = 0

                            selected_domain = st.selectbox(
                                "Domain *",
                                options=domain_list,
                                index=domain_index,
                                key="modify_domain",
                                help="Select the domain related to the problem",
                            )
                            selected_domain_id = (
                                domain_options.get(selected_domain)
                                if selected_domain != "Select a domain..."
                                else None
                            )

                            # Detect if domain changed to reset specialties
                            if st.session_state[f"previous_domain_id_{ticket_id}"] != selected_domain_id:
                                st.session_state[f"edit_form_specialties_{ticket_id}"] = []
                                st.session_state[f"previous_domain_id_{ticket_id}"] = selected_domain_id

                        else:
                            st.warning("No domains available")
                            selected_domain = None
                            selected_domain_id = None

                        # Specialties field (multi-selection dependent on selected domain)
                        selected_specialties = []
                        selected_specialty_ids = []
                        if selected_domain_id:
                            specialties = load_specialties_by_domain(selected_domain_id)
                            if specialties:
                                specialty_options = {s["name"]: s["id"] for s in specialties}

                                # Filter default specialties to keep only those that exist for this domain
                                valid_default_specialties = [
                                    spec
                                    for spec in st.session_state[f"edit_form_specialties_{ticket_id}"]
                                    if spec in specialty_options.keys()
                                ]

                                selected_specialties = st.multiselect(
                                    "Specialties",
                                    options=list(specialty_options.keys()),
                                    default=valid_default_specialties,
                                    key="modify_specialties",
                                    help="Select the relevant specialties",
                                )
                                selected_specialty_ids = [
                                    specialty_options[name] for name in selected_specialties
                                ]

                                # Update session state
                                st.session_state[f"edit_form_specialties_{ticket_id}"] = selected_specialties
                            else:
                                st.info("No specialties available for this domain")
                        else:
                            st.info("First select a domain to see specialties")

                        # Update selected domain in session
                        if selected_domain:
                            st.session_state[f"edit_form_domain_{ticket_id}"] = selected_domain

                        # Display creation info
                        st.info(
                            f"**Created by:** {ticket['created_by_name'] or 'Unknown'}"
                        )
                        st.info(f"**Creation date:** {ticket['created_at']}")

                    new_problem_desc = st.text_area(
                        "Problem Description *",
                        value=ticket["problem_desc"],
                        height=150,
                        key="modify_problem_desc",
                        help="Describe in detail the problem encountered by the customer",
                    )

                    submitted = st.form_submit_button("💾 Update", type="primary")

                    if submitted:
                        # Validate required fields
                        errors = []
                        if not new_customer_name:
                            errors.append("Customer name")
                        if not new_customer_phone:
                            errors.append("Customer phone")
                        if not new_problem_desc:
                            errors.append("Problem description")
                        if not selected_domain_id:
                            errors.append("A domain")
                        if payment == "Yes" and (amount is None or amount <= 0):
                            errors.append("Payment amount (must be greater than 0)")

                        if errors:
                            st.error(
                                f"⚠️ The following fields are required: {', '.join(errors)}"
                            )
                        else:
                            # Update ticket with all fields
                            try:
                                success, message = db_manager.update_problem(
                                    problem_id=ticket_id,
                                    customer_name=new_customer_name.strip(),
                                    customer_phone=new_customer_phone.strip(),
                                    problem_desc=new_problem_desc.strip(),
                                    is_paid=1 if payment == "Yes" else 0,
                                    amount=amount if payment == "Yes" else 0,
                                    craft_ids=str(selected_domain_id) if selected_domain_id else None,
                                    speciality_ids=",".join(map(str, selected_specialty_ids)) if selected_specialty_ids else None,
                                    updated_by=st.session_state.user_id,
                                )

                                if success:
                                    st.success(f"✅ {message}")
                                    
                                    # Clear session state for this ticket
                                    keys_to_clear = [
                                        f"edit_form_payment_{ticket_id}",
                                        f"edit_form_amount_{ticket_id}",
                                        f"edit_form_domain_{ticket_id}",
                                        f"edit_form_specialties_{ticket_id}",
                                        f"previous_domain_id_{ticket_id}"
                                    ]
                                    for key in keys_to_clear:
                                        if key in st.session_state:
                                            del st.session_state[key]
                                    
                                    clear_cache()
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")

                            except Exception as e:
                                st.error(f"❌ Error during update: {str(e)}")

                # Update session variables
                st.session_state[f"edit_form_payment_{ticket_id}"] = payment
                if amount is not None:
                    st.session_state[f"edit_form_amount_{ticket_id}"] = amount
    else:
        current_user_role = PermissionManager.get_user_role()
        if current_user_role == 'agent':
            st.info("No tickets available for editing. You can only edit tickets that you have created.")
        else:
            st.info("No tickets available for editing.")
