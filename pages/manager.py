import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import random
import re
import time

# Ajouter le répertoire parent au path pour importer database et permissions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import db_manager
from permissions import PermissionManager

# Email validation function
def is_valid_email(email):
    """Validates email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")  # Redirect to home/login if not connected

# Check page access permissions
if not PermissionManager.check_page_access('manager_page'):
    PermissionManager.show_access_denied("You do not have the necessary permissions to access this page.")

"""Manager management page"""
st.title("👨‍💼 Manager Management")

# Define data loading functions
def load_managers_data():
    """Load managers data from database"""
    try:
        # Get all users with "manager" role
        users = db_manager.get_all_users()
        if users:
            df = pd.DataFrame(users)
            # Filter only managers
            managers_df = df[df['role_name'] == 'manager'].copy()
            # Convert dates
            if 'created_at' in managers_df.columns:
                managers_df['created_at'] = pd.to_datetime(managers_df['created_at'])
            if 'updated_at' in managers_df.columns:
                managers_df['updated_at'] = pd.to_datetime(managers_df['updated_at'])
            return managers_df
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['id', 'nin', 'name', 'email', 'role_name', 'is_active', 'created_at'])
    except Exception as e:
        st.error(f"Error loading managers: {str(e)}")
        return pd.DataFrame(columns=['id', 'nin', 'name', 'email', 'role_name', 'is_active', 'created_at'])

def load_roles_data():
    """Load roles data from database"""
    try:
        roles = db_manager.get_all_roles()
        return roles if roles else []
    except Exception as e:
        st.error(f"Error loading roles: {str(e)}")
        return []

# Get available tabs according to permissions
available_tabs = PermissionManager.get_available_tabs('manager_page')

if not available_tabs:
    st.error("No tabs available for your role.")
    st.stop()

# Create tabs dynamically
tabs = st.tabs(available_tabs)

# Load roles globally for reuse
roles = load_roles_data()

# List Tab
if "📋 List" in available_tabs:
    tab_index = available_tabs.index("📋 List")
    with tabs[tab_index]:
        st.subheader("Manager List")

        # Load managers data
        managers_df = load_managers_data()
        
        # In the List tab, we display all managers for all users
        # (no permission filtering here)
        
        # Filters and search
        col1, col2 = st.columns(2)

        with col1:
            search_manager = st.text_input("🔍 Search", placeholder="Name, email, ID...")

        with col2:
            status_filter = st.selectbox("Filter by status", ["All", "Active", "Inactive"])
        
        # Filter data if necessary
        filtered_df = managers_df.copy()
        if not filtered_df.empty:
            # Filter by search (name, email, ID)
            if search_manager.strip():
                search_term = search_manager.strip().lower()
                filtered_df = filtered_df[
                    filtered_df['name'].str.lower().str.contains(search_term, na=False) |
                    filtered_df['email'].str.lower().str.contains(search_term, na=False) |
                    filtered_df['id'].astype(str).str.contains(search_term, na=False)
                ]
            
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
            total_managers = len(display_df)
            
            # Pagination configuration
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.info(f"📊 **{total_managers}** manager(s) found")
            
            with col2:
                managers_per_page = st.selectbox(
                    "Managers per page", 
                    [10, 25, 50, 100], 
                    index=1,  # Default 25
                    key="managers_per_page_list"
                )
            
            with col3:
                total_pages = max(1, (total_managers - 1) // managers_per_page + 1)
                current_page = st.number_input(
                    f"Page (1-{total_pages})", 
                    min_value=1, 
                    max_value=total_pages, 
                    value=1,
                    key="current_page_managers"
                )
            
            # Calculate indices for pagination
            start_idx = (current_page - 1) * managers_per_page
            end_idx = min(start_idx + managers_per_page, total_managers)
            
            # Display paginated data
            paginated_df = display_df.iloc[start_idx:end_idx]
            
            # Display pagination information
            st.caption(f"Showing managers {start_idx + 1} to {end_idx} of {total_managers}")
            
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

# Add Tab
if "➕ Add" in available_tabs:
    tab_index = available_tabs.index("➕ Add")
    with tabs[tab_index]:
        st.subheader("Add a Manager")
        with st.form("add_manager_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full name *", placeholder="Ex: John Doe")
                email = st.text_input("Email *", placeholder="john.doe@fixtop.com")
                nin = st.text_input("NIN", placeholder="Identification number (optional)")
            with col2:
                # Limit role options to "manager" only
                role_options_add = ["manager"]
                selected_role = st.selectbox("Role *", role_options_add)
                password = st.text_input("Password *", type="password", placeholder="Secure password")
                confirm_password = st.text_input("Confirm password *", type="password", placeholder="Confirm password")
            
            submitted = st.form_submit_button("Create manager")
            if submitted:
                if not name.strip() or not email.strip() or not password or not confirm_password:
                    st.error("❌ All fields marked with * are required")
                elif not is_valid_email(email):
                    st.error("❌ Invalid email format")
                elif password != confirm_password:
                    st.error("❌ Passwords do not match")
                elif len(password) < 6:
                    st.error("❌ Password must contain at least 6 characters")
                else:
                    # Password strength validation
                    is_strong, errors = db_manager.validate_password_strength(password)
                    if not is_strong:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        # Get role_id from role_name
                        role_id = next((role['id'] for role in roles if role['name'] == selected_role), None)
                        if not role_id:
                            st.error("❌ Invalid role")
                        else:
                            created_by = st.session_state.get('user_id', 1)  # ID of connected user
                            # Use create_user instead of add_user
                            success, message, _ = db_manager.create_user(
                                name=name.strip(),
                                email=email.strip().lower(),
                                password=password,
                                role_id=role_id,
                                nin=nin.strip() if nin.strip() else None,
                                created_by=created_by
                            )
                            if success:
                                st.success(f"✅ {message}")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")

# Edit Tab
if "✏️ Edit" in available_tabs:
    tab_index = available_tabs.index("✏️ Edit")
    with tabs[tab_index]:
        st.subheader("Edit a Manager")
        managers_df = load_managers_data()
        
        # Filter data according to permissions (same logic as List tab)
        if PermissionManager.get_user_role() == 'manager' and not PermissionManager.has_permission('manager_page', 'can_view_all'):
            # If user cannot see all managers, filter for their own data
            user_id = PermissionManager.get_user_id()
            if user_id and not managers_df.empty:
                managers_df = managers_df[managers_df['id'] == user_id]
        
        if not managers_df.empty:
            manager_options = managers_df.apply(lambda x: f"{x['name']} ({x['email']}) - ID={x['id']}", axis=1).tolist()
            
            # If only one manager (their own), automatic selection
            if len(manager_options) == 1:
                st.info(f"📝 Editing your profile: {manager_options[0]}")
                selected_option = manager_options[0]
            else:
                selected_option = st.selectbox("Choose a manager", manager_options)
            
            selected_manager_id = int(selected_option.split("ID=")[-1])
            
            # Check if user has the right to edit this specific manager
            current_user_id = PermissionManager.get_user_id()
            current_user_role = PermissionManager.get_user_role()
            
            # If user is a manager and doesn't have permission to see all,
            # they can only edit their own information
            if (current_user_role == 'manager' and 
                not PermissionManager.has_permission('manager_page', 'can_view_all') and 
                selected_manager_id != current_user_id):
                st.error("❌ You do not have permissions to edit this manager.")
                st.info("💡 You can only edit your own information.")
                st.stop()
            
            manager_data = managers_df[managers_df['id'] == selected_manager_id].iloc[0]
            
            # Display current information
            with st.expander("📋 Current Information", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Name:** {manager_data['name']}")
                    st.write(f"**Email:** {manager_data['email']}")
                    st.write(f"**NIN:** {manager_data.get('nin', 'Not provided')}")
                with col2:
                    st.write(f"**Role:** {manager_data.get('role_name', 'Not defined')}")
                    status_text = "Active" if manager_data['is_active'] == 1 else "Inactive"
                    st.write(f"**Status:** {status_text}")
                    st.write(f"**Created on:** {manager_data.get('created_at', 'Not available')}")
            
            # Checkbox outside form to allow immediate interaction
            change_password = st.checkbox("Change password", key=f"change_password_{selected_manager_id}")
            
            with st.form(f"edit_manager_form_{selected_manager_id}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Full name *", value=manager_data['name'] or "")
                    new_email = st.text_input("Email *", value=manager_data['email'] or "")
                    new_nin = st.text_input("NIN", value=manager_data['nin'] or "")
                with col2:
                    # Limit role options to "manager" only
                    role_options_edit = ["manager"]
                    current_role_index = 0  # Always 0 since there's only one option
                    new_role = st.selectbox("Role *", role_options_edit, index=current_role_index)
                    new_status = st.selectbox("Status", ["Active", "Inactive"], index=0 if manager_data['is_active'] == 1 else 1)
                    new_password = st.text_input("New password", type="password", placeholder="New secure password" if change_password else "Check 'Change password' to activate", disabled=not change_password)
                    confirm_new_password = st.text_input("Confirm new password", type="password", placeholder="Confirm new password" if change_password else "Check 'Change password' to activate", disabled=not change_password)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    update_submitted = st.form_submit_button("💾 Update", type="primary")
                with col2:
                    if st.form_submit_button("🔄 Reset"):
                        st.rerun()
                with col3:
                    if manager_data['is_active'] == 1:
                        deactivate_submitted = st.form_submit_button("🔒 Deactivate", type="secondary")
                    else:
                        activate_submitted = st.form_submit_button("✅ Activate", type="secondary")
                
                if update_submitted:
                    if not new_name.strip() or not new_email.strip():
                        st.error("❌ Name and email are required")
                    elif not is_valid_email(new_email):
                        st.error("❌ Invalid email format")
                    elif change_password and (not new_password or len(new_password) < 6):
                        st.error("❌ Password must contain at least 6 characters")
                    elif change_password and new_password != confirm_new_password:
                        st.error("❌ Passwords do not match")
                    else:
                        # Password strength validation if changed
                        validation_passed = True
                        if change_password and new_password:
                            is_strong, errors = db_manager.validate_password_strength(new_password)
                            if not is_strong:
                                for error in errors:
                                    st.error(f"❌ {error}")
                                validation_passed = False
                        
                        if validation_passed:
                            # Get role_id from new_role
                            new_role_id = next((role['id'] for role in roles if role['name'] == new_role), None)
                            if not new_role_id:
                                st.error("❌ Invalid role")
                            else:
                                updated_by = st.session_state.get('user_id', 1)
                                # Corrected call to update_user with named parameters
                                success, message = db_manager.update_user(
                                    user_id=selected_manager_id,
                                    name=new_name.strip(),
                                    email=new_email.strip().lower(),
                                    role_id=new_role_id,
                                    nin=new_nin.strip() if new_nin.strip() else None,
                                    is_active=1 if new_status == "Active" else 0,
                                    updated_by=updated_by
                                )
                                
                                # Update password separately if necessary
                                if success and change_password and new_password:
                                    hashed_password = db_manager.hash_password(new_password)
                                    with db_manager.get_connection() as conn:
                                        conn.execute("UPDATE user SET password = ? WHERE id = ?", (hashed_password, selected_manager_id))
                                        conn.commit()
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
            
            # Handle deactivation/activation
            if 'deactivate_submitted' in locals() and deactivate_submitted:
                success, message = db_manager.update_user(selected_manager_id, is_active=0, updated_by=st.session_state.get('user_id', 1))
                if success:
                    st.success(f"✅ {message}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            
            if 'activate_submitted' in locals() and activate_submitted:
                success, message = db_manager.update_user(selected_manager_id, is_active=1, updated_by=st.session_state.get('user_id', 1))
                if success:
                    st.success(f"✅ {message}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        
        else:
            st.info("No managers found matching your permissions.")

# Statistics Tab
if "📊 Statistics" in available_tabs:
    tab_index = available_tabs.index("📊 Statistics")
    with tabs[tab_index]:
        st.subheader("Manager Statistics")
        try:
            stats = db_manager.get_user_stats()
            # Filter for managers if necessary
            manager_stats = {k: v for k, v in stats.items() if k != 'by_role'}
            manager_by_role = [r for r in stats['by_role'] if r['name'] == 'manager']
            manager_stats['by_role'] = manager_by_role if manager_by_role else [{'name': 'manager', 'count': 0}]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Managers", manager_stats['total'])
            with col2:
                st.metric("Active", manager_stats['active'])
            with col3:
                st.metric("Inactive", manager_stats['inactive'])
            
            if manager_stats['by_role']:
                df_stats = pd.DataFrame(manager_stats['by_role'])
                st.subheader("Managers by Role")
                st.dataframe(df_stats)
        except Exception as e:
            st.error(f"Error loading statistics: {str(e)}")
            st.info("Statistics feature to be implemented")