import streamlit as st
from database import db_manager
from services.tickets.data_loader import load_domains, load_specialties_by_domain
from services.cache_utils import clear_cache

def display():
    st.header("Add a New Ticket")

    # Load domains for the form
    domains = load_domains()

    # Initialize session variables for the form
    if "form_customer_name" not in st.session_state:
        st.session_state.form_customer_name = ""
    if "form_customer_phone" not in st.session_state:
        st.session_state.form_customer_phone = ""
    if "form_problem_desc" not in st.session_state:
        st.session_state.form_problem_desc = ""
    if "form_payment" not in st.session_state:
        st.session_state.form_payment = "No"
    if "form_amount" not in st.session_state:
        st.session_state.form_amount = 0
    if "form_domain" not in st.session_state:
        st.session_state.form_domain = "Select a domain..."
    if "form_specialties" not in st.session_state:
        st.session_state.form_specialties = []
    if "previous_domain_id" not in st.session_state:
        st.session_state.previous_domain_id = None

    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input(
            "Customer Name *",
            value=st.session_state.form_customer_name,
            key="add_customer_name",
        )
        customer_phone = st.text_input(
            "Customer Phone *",
            value=st.session_state.form_customer_phone,
            key="add_customer_phone",
        )

        # Payment field
        payment = st.selectbox(
            "Payment *",
            options=["No", "Yes"],
            index=0 if st.session_state.form_payment == "No" else 1,
            key="add_payment",
            help="Has the customer made a payment?",
        )

        # Immediate amount update when payment = "No"
        if payment == "No":
            st.session_state.form_amount = 0

        # Amount field (conditional) - displays immediately
        amount = None
        if payment == "Yes":
            amount = st.number_input(
                "Amount (₦) *",
                min_value=0,
                step=1,
                value=int(st.session_state.form_amount),
                key="add_amount",
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

    with col2:
        # Domain field (simple selection)
        if domains:
            domain_options = {d["name"]: d["id"] for d in domains}
            domain_list = ["Select a domain..."] + list(domain_options.keys())

            try:
                domain_index = domain_list.index(st.session_state.form_domain)
            except ValueError:
                domain_index = 0

            selected_domain = st.selectbox(
                "Domain *",
                options=domain_list,
                index=domain_index,
                key="add_domain",
                help="Select the domain related to the problem",
            )
            selected_domain_id = (
                domain_options.get(selected_domain)
                if selected_domain != "Select a domain..."
                else None
            )

            # Detect if domain changed to reset specialties
            if "previous_domain_id" not in st.session_state:
                st.session_state.previous_domain_id = None

            if st.session_state.previous_domain_id != selected_domain_id:
                st.session_state.form_specialties = []
                st.session_state.previous_domain_id = selected_domain_id

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
                    for spec in st.session_state.form_specialties
                    if spec in specialty_options.keys()
                ]

                selected_specialties = st.multiselect(
                    "Specialties",
                    options=list(specialty_options.keys()),
                    default=valid_default_specialties,
                    key="add_specialties",
                    help="Select the relevant specialties",
                )
                selected_specialty_ids = [
                    specialty_options[name] for name in selected_specialties
                ]

                # Immediate session update to avoid double-click
                st.session_state.form_specialties = selected_specialties
            else:
                st.info("No specialties available for this domain")
        else:
            st.info("First select a domain to see specialties")

        # Immediate update of selected domain
        if selected_domain:
            st.session_state.form_domain = selected_domain

    problem_desc = st.text_area(
        "Problem Description *",
        height=150,
        value=st.session_state.form_problem_desc,
        key="add_problem_desc",
        help="Describe in detail the problem encountered by the customer",
    )

    # Action buttons
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

    with col_btn1:
        if st.button("➕ Create Ticket", type="primary", key="create_ticket_btn"):
            # Validate required fields
            errors = []
            if not customer_name:
                errors.append("Customer name")
            if not customer_phone:
                errors.append("Customer phone")
            if not problem_desc:
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
                # Create ticket with new fields
                try:
                    success, message, problem_id = db_manager.create_problem(
                        customer_name=customer_name.strip(),
                        customer_phone=customer_phone.strip(),
                        problem_desc=problem_desc.strip(),
                        created_by=st.session_state.user_id,
                        is_paid=1 if payment == "Yes" else 0,
                        amount=amount if payment == "Yes" else 0,
                        craft_ids=str(selected_domain_id) if selected_domain_id else None,
                        speciality_ids=",".join(map(str, selected_specialty_ids)) if selected_specialty_ids else None,
                        updated_by=st.session_state.user_id
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        
                        # Reset form
                        st.session_state.form_customer_name = ""
                        st.session_state.form_customer_phone = ""
                        st.session_state.form_problem_desc = ""
                        st.session_state.form_payment = "No"
                        st.session_state.form_amount = 0
                        st.session_state.form_domain = "Select a domain..."
                        st.session_state.form_specialties = []
                        st.session_state.previous_domain_id = None

                        clear_cache()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

                except Exception as e:
                    st.error(f"❌ Error during creation: {str(e)}")

    with col_btn2:
        if st.button("🔄 Reset", key="reset_form_btn"):
            # Reset all form fields
            st.session_state.form_customer_name = ""
            st.session_state.form_customer_phone = ""
            st.session_state.form_problem_desc = ""
            st.session_state.form_payment = "No"
            st.session_state.form_amount = 0
            st.session_state.form_domain = "Select a domain..."
            st.session_state.form_specialties = []
            st.session_state.previous_domain_id = None
            st.rerun()

    # Update session variables (only for fields not managed immediately)
    st.session_state.form_customer_name = customer_name
    st.session_state.form_customer_phone = customer_phone
    st.session_state.form_problem_desc = problem_desc
    st.session_state.form_payment = payment
    if amount is not None:
        st.session_state.form_amount = amount
