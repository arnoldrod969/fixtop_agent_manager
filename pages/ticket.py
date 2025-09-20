import streamlit as st
import pandas as pd
from datetime import datetime
from database import db_manager
from permissions import PermissionManager

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")  # Redirect to home/login if not connected

# Check page access permissions
if not PermissionManager.check_page_access('ticket_page'):
    PermissionManager.show_access_denied("You do not have access to ticket management.")

# Page configuration
st.set_page_config(
    page_title="Ticket Management",
    page_icon="🎫",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .ticket-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-active {
        color: #28a745;
        font-weight: bold;
    }
    .status-inactive {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.title("🎫 Ticket Management")
st.markdown("---")

# Utility functions
@st.cache_data(ttl=60)
def load_tickets():
    """Loads all tickets from the database"""
    return db_manager.get_all_problems()

@st.cache_data(ttl=60)
def load_ticket_stats():
    """Loads ticket statistics"""
    return db_manager.get_problem_stats()

@st.cache_data(ttl=60)
def load_domains():
    """Loads all domains from the database"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name FROM craft 
                WHERE is_active = 1 
                ORDER BY name
            """)
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        st.error(f"Error loading domains: {str(e)}")
        return []

@st.cache_data(ttl=60)
def load_specialties_by_domain(domain_id):
    """Loads specialties for the selected domain"""
    if not domain_id:
        return []
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name FROM speciality 
                WHERE craft_id = ? AND is_active = 1 
                ORDER BY name
            """, (domain_id,))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        st.error(f"Error loading specialties: {str(e)}")
        return []

def clear_cache():
    """Clears cache to refresh data"""
    st.cache_data.clear()

# Create tabs based on permissions
available_tabs = PermissionManager.get_available_tabs('ticket_page')

# Dynamic tab creation according to permissions
tabs = st.tabs(available_tabs)

# Tab variable initialization
tab1 = tab2 = tab3 = tab4 = tab5 = None

# Tab assignment according to their content
for i, tab_name in enumerate(available_tabs):
    if "List" in tab_name:
        tab1 = tabs[i]
    elif "Add" in tab_name:
        tab2 = tabs[i]
    elif "Edit" in tab_name:
        tab3 = tabs[i]
    elif "Delete" in tab_name:
        tab4 = tabs[i]
    elif "Statistics" in tab_name:
        tab5 = tabs[i]

# ==================== LIST TAB ====================
with tab1:
    st.header("Ticket List")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_customer = st.text_input("🔍 Search by customer name", key="search_customer")
    
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
            filtered_tickets = [t for t in filtered_tickets 
                              if search_customer.lower() in t['customer_name'].lower()]
        
        if search_phone:
            filtered_tickets = [t for t in filtered_tickets 
                              if search_phone in t['customer_phone']]
        
        # Results display
        st.info(f"📊 {len(filtered_tickets)} ticket(s) found")
        
        # Ticket table
        if filtered_tickets:
            df = pd.DataFrame(filtered_tickets)
            
            # Select columns to display
            display_columns = ['id', 'customer_name', 'customer_phone', 'problem_desc', 
                             'created_by_name', 'created_at']
            
            # Column renaming for display
            column_names = {
                'id': 'ID',
                'customer_name': 'Customer Name',
                'customer_phone': 'Phone',
                'problem_desc': 'Problem Description',
                'created_by_name': 'Created by',
                'created_at': 'Creation Date'
            }
            
            df_display = df[display_columns].rename(columns=column_names)
            
            # Dataframe display configuration
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Problem Description": st.column_config.TextColumn(
                        width="large"
                    ),
                    "Creation Date": st.column_config.DatetimeColumn(
                        format="DD/MM/YYYY HH:mm"
                    )
                }
            )
        else:
            st.warning("No tickets match the search criteria.")
    else:
        st.info("No tickets found in the database.")

# ==================== ADD TAB ====================
if tab2 is not None:  # Only if user has permissions
    with tab2:
        st.header("Add a New Ticket")
        
        # Load domains for the form
        domains = load_domains()
        
        # Initialize session variables for the form
        if 'form_customer_name' not in st.session_state:
            st.session_state.form_customer_name = ""
        if 'form_customer_phone' not in st.session_state:
            st.session_state.form_customer_phone = ""
        if 'form_problem_desc' not in st.session_state:
            st.session_state.form_problem_desc = ""
        if 'form_payment' not in st.session_state:
            st.session_state.form_payment = "No"
        if 'form_amount' not in st.session_state:
            st.session_state.form_amount = 0
        if 'form_domain' not in st.session_state:
            st.session_state.form_domain = "Select a domain..."
        if 'form_specialties' not in st.session_state:
            st.session_state.form_specialties = []
        if 'previous_domain_id' not in st.session_state:
            st.session_state.previous_domain_id = None
        
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input(
                "Customer Name *", 
                value=st.session_state.form_customer_name,
                key="add_customer_name"
            )
            customer_phone = st.text_input(
                "Customer Phone *", 
                value=st.session_state.form_customer_phone,
                key="add_customer_phone"
            )
            
            # Payment field
            payment = st.selectbox(
                "Payment *",
                options=["No", "Yes"],
                index=0 if st.session_state.form_payment == "No" else 1,
                key="add_payment",
                help="Has the customer made a payment?"
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
                    help="Payment amount in naira"
                )
            else:
                # Display amount at 0 when payment = "No"
                st.number_input(
                    "Amount (₦)",
                    value=0,
                    disabled=True,
                    help="Amount is 0 because no payment was made"
                )
        
        with col2:
            # Domain field (simple selection)
            if domains:
                domain_options = {d['name']: d['id'] for d in domains}
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
                    help="Select the domain related to the problem"
                )
                selected_domain_id = domain_options.get(selected_domain) if selected_domain != "Select a domain..." else None
                
                # Detect if domain changed to reset specialties
                if 'previous_domain_id' not in st.session_state:
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
                    specialty_options = {s['name']: s['id'] for s in specialties}
                    
                    # Filter default specialties to keep only those that exist for this domain
                    valid_default_specialties = [spec for spec in st.session_state.form_specialties 
                                                if spec in specialty_options.keys()]
                    
                    selected_specialties = st.multiselect(
                        "Specialties",
                        options=list(specialty_options.keys()),
                        default=valid_default_specialties,
                        key="add_specialties",
                        help="Select the relevant specialties"
                    )
                    selected_specialty_ids = [specialty_options[name] for name in selected_specialties]
                    
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
            help="Describe in detail the problem encountered by the customer"
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
                    st.error(f"⚠️ The following fields are required: {', '.join(errors)}")
                else:
                    # Create ticket with new fields
                    try:
                        with db_manager.get_connection() as conn:
                            # Insert main ticket
                            cursor = conn.execute("""
                                 INSERT INTO problems (customer_name, customer_phone, problem_desc, 
                                                     is_paid, amount, craft_ids, speciality_ids, created_by , updated_by)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ? , ?)
                             """, (
                                 customer_name.strip(),
                                 customer_phone.strip(),
                                 problem_desc.strip(),
                                 1 if payment == "Yes" else 0,
                                 amount if payment == "Yes" else 0,
                                 str(selected_domain_id) if selected_domain_id else None,
                                 ','.join(map(str, selected_specialty_ids)) if selected_specialty_ids else None,
                                 st.session_state.user_id,
                                 st.session_state.user_id
                             ))
                            
                            problem_id = cursor.lastrowid
                            
                            conn.commit()
                            st.success(f"✅ Ticket created successfully (ID: {problem_id})")
                            
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

# ==================== EDIT TAB ====================
if tab3 is not None:  # Only if user has permissions
    with tab3:
        st.header("Edit a Ticket")
        
        tickets = load_tickets()
        
        if tickets:
            # Select ticket to edit
            ticket_options = {f"#{t['id']} - {t['customer_name']} ({t['customer_phone']})": t['id'] 
                             for t in tickets}
            
            selected_ticket_key = st.selectbox(
                "Select a ticket to edit",
                options=list(ticket_options.keys()),
                key="modify_ticket_select"
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
                                value=ticket['customer_name'],
                                key="modify_customer_name"
                            )
                            new_customer_phone = st.text_input(
                                "Customer Phone", 
                                value=ticket['customer_phone'],
                                key="modify_customer_phone"
                            )
                        
                        with col2:
                            st.info(f"**Created by:** {ticket['created_by_name'] or 'Unknown'}")
                            st.info(f"**Creation date:** {ticket['created_at']}")
                        
                        new_problem_desc = st.text_area(
                            "Problem Description", 
                            value=ticket['problem_desc'],
                            height=150,
                            key="modify_problem_desc"
                        )
                        
                        submitted = st.form_submit_button("💾 Update", type="primary")
                        
                        if submitted:
                            if not new_customer_name or not new_customer_phone or not new_problem_desc:
                                st.error("⚠️ All fields are required.")
                            else:
                                # Update ticket
                                success, message = db_manager.update_problem(
                                    problem_id=ticket_id,
                                    customer_name=new_customer_name.strip(),
                                    customer_phone=new_customer_phone.strip(),
                                    problem_desc=new_problem_desc.strip(),
                                    updated_by=st.session_state.user_id
                                )
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    clear_cache()
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
        else:
            st.info("No tickets available for editing.")

# ==================== DELETE TAB ====================
if tab4 is not None:  # Only if user has permissions
    with tab4:
        st.header("Delete a Ticket")
        st.warning("⚠️ Warning: This action will mark the ticket as inactive (logical deletion).")
        
        tickets = load_tickets()
        
        if tickets:
            # Ticket selection for deletion
            ticket_options = {f"#{t['id']} - {t['customer_name']} ({t['customer_phone']})": t['id'] 
                             for t in tickets}
            
            selected_ticket_key = st.selectbox(
                "Select a ticket to delete",
                options=list(ticket_options.keys()),
                key="delete_ticket_select"
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
                        st.write(f"**Created by:** {ticket['created_by_name'] or 'Unknown'}")
                        st.write(f"**Date:** {ticket['created_at']}")
                    
                    st.write(f"**Problem:** {ticket['problem_desc']}")
                    
                    # Deletion confirmation
                    col1, col2, col3 = st.columns([1, 1, 2])
                    
                    with col1:
                        if st.button("🗑️ Confirm Deletion", type="primary", key="confirm_delete"):
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

# ==================== STATISTICS TAB ====================
if tab5 is not None:
    with tab5:
        st.header("Ticket Statistics")
        
        # Load statistics
        stats = load_ticket_stats()
        
        # Main metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📊 Total Tickets</h3>
                <h2>{stats['total']}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📅 Today</h3>
                <h2>{stats['today']}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_per_month = sum([m['count'] for m in stats['by_month']]) / max(len(stats['by_month']), 1)
            st.markdown(f"""
            <div class="metric-card">
                <h3>📈 Average/Month</h3>
                <h2>{avg_per_month:.1f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Monthly tickets chart
        if stats['by_month']:
            st.subheader("📈 Ticket Evolution by Month")
            
            df_months = pd.DataFrame(stats['by_month'])
            df_months['month'] = pd.to_datetime(df_months['month'])
            df_months = df_months.sort_values('month')
            
            st.line_chart(
                df_months.set_index('month')['count'],
                use_container_width=True
            )
            
            # Detailed table
            st.subheader("📋 Monthly Details")
            df_display = df_months.copy()
            df_display['month'] = df_display['month'].dt.strftime('%B %Y')
            df_display.columns = ['Month', 'Number of Tickets']
            
            st.dataframe(
                  df_display,
                  use_container_width=True,
                  hide_index=True
              )
        else:
            st.info("No data available for charts.")
        
        # Refresh button
        if st.button("🔄 Refresh Statistics", key="refresh_stats"):
            clear_cache()
            st.rerun()