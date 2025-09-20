import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import random
import re
import time

# Add parent directory to path to import database and permissions
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
if not PermissionManager.check_page_access('user_page'):
    PermissionManager.show_access_denied("This page is reserved for administrators.")

"""User management page"""
st.title("👥 User Management")

# Define data loading functions
def load_users_data():
    """Loads user data from the database"""
    try:
        users = db_manager.get_all_users()
        if users:
            df = pd.DataFrame(users)
            # Convert dates
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
            if 'updated_at' in df.columns:
                df['updated_at'] = pd.to_datetime(df['updated_at'])
            return df
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['id', 'nin', 'name', 'email', 'role_name', 'is_active', 'created_at'])
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")
        return pd.DataFrame(columns=['id', 'nin', 'name', 'email', 'role_name', 'is_active', 'created_at'])

def load_roles_data():
    """Loads role data from the database"""
    try:
        roles = db_manager.get_all_roles()
        return roles if roles else []
    except Exception as e:
        st.error(f"Error loading roles: {str(e)}")
        return []

# Get available tabs according to permissions
available_tabs = PermissionManager.get_available_tabs('user_page')

if not available_tabs:
    st.error("No tabs available for your role.")
    st.stop()

# Create tabs dynamically
tabs = st.tabs(available_tabs)

# Load roles globally to reuse in tabs
roles = load_roles_data()

# List Tab
if "📋 List" in available_tabs:
    tab_index = available_tabs.index("📋 List")
    with tabs[tab_index]:
        st.subheader("User List")

        # Load user data
        users_df = load_users_data()
        
        # Create role filter options dynamically
        role_options = ["All"]
        if roles:
            role_options.extend([role['name'] for role in roles])
        
        # Filters and search
        col1, col2, col3 = st.columns(3)

        with col1:
            search_user = st.text_input("🔍 Search", placeholder="Name, email, ID...")

        with col2:
            role_filter = st.selectbox("Filter by role", role_options)

        with col3:
            status_filter = st.selectbox("Filter by status", ["All", "Active", "Inactive"])
        
        # Filter data if necessary
        filtered_df = users_df.copy()
        if not filtered_df.empty:
            # Filter by search (name, email, ID)
            if search_user.strip():
                search_term = search_user.strip().lower()
                filtered_df = filtered_df[
                    filtered_df['name'].str.lower().str.contains(search_term, na=False) |
                    filtered_df['email'].str.lower().str.contains(search_term, na=False) |
                    filtered_df['id'].astype(str).str.contains(search_term, na=False)
                ]
            
            # Filter by role
            if role_filter != "All":
                filtered_df = filtered_df[filtered_df['role_name'] == role_filter]
            
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
            total_users = len(display_df)
            
            # Pagination configuration
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.info(f"📊 **{total_users}** user(s) found")
            
            with col2:
                users_per_page = st.selectbox(
                    "Users per page", 
                    [10, 25, 50, 100], 
                    index=1,  # Default 25
                    key="users_per_page_list"
                )
            
            with col3:
                total_pages = max(1, (total_users - 1) // users_per_page + 1)
                current_page = st.number_input(
                    f"Page (1-{total_pages})", 
                    min_value=1, 
                    max_value=total_pages, 
                    value=1,
                    key="current_page_list"
                )
            
            # Calculate indices for pagination
            start_idx = (current_page - 1) * users_per_page
            end_idx = min(start_idx + users_per_page, total_users)
            
            # Display paginated data
            paginated_df = display_df.iloc[start_idx:end_idx]
            
            # Display pagination information
            st.caption(f"Showing users {start_idx + 1} to {end_idx} of {total_users}")
            
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
            
            # Batch actions
            st.subheader("Batch Actions")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.button("📧 Send Email")
            with col2:
                st.button("⏸️ Suspend Selection")
            with col3:
                st.button("✅ Activate Selection")
            with col4:
                st.button("📤 Export List")

# Add Tab
if "➕ Add" in available_tabs:
    tab_index = available_tabs.index("➕ Add")
    with tabs[tab_index]:
        st.subheader("Add a User")
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full name *", placeholder="Ex: John Doe")
                email = st.text_input("Email *", placeholder="john.doe@fixtop.com")
                nin = st.text_input("NIN", placeholder="Identification number (optional)")
            with col2:
                role_options_add = [role['name'] for role in roles] if roles else []
                selected_role = st.selectbox("Role *", role_options_add)
                password = st.text_input("Password *", type="password", placeholder="Secure password")
                confirm_password = st.text_input("Confirm password *", type="password", placeholder="Confirm password")
            
            submitted = st.form_submit_button("Create user")
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
                            created_by = st.session_state.get('user_id', 1)  # Connected user ID
                            # Corrected call to add_user (param order: nin, name, email, password, role_name, created_by)
                            success, message, _ = db_manager.add_user(
                                nin=nin.strip() if nin.strip() else None,
                                name=name.strip(),
                                email=email.strip().lower(),
                                password=password,
                                role_name=selected_role,
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
        st.subheader("Edit a User")
        users_df = load_users_data()
        if not users_df.empty:
            user_options = users_df.apply(lambda x: f"{x['name']} ({x['email']}) - ID={x['id']}", axis=1).tolist()
            selected_option = st.selectbox("Choose a user", user_options)
            selected_user_id = int(selected_option.split("ID=")[-1])
            user_data = users_df[users_df['id'] == selected_user_id].iloc[0]
            
            # Display current information
            with st.expander("📋 Current information", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Name:** {user_data['name']}")
                    st.write(f"**Email:** {user_data['email']}")
                    st.write(f"**NIN:** {user_data.get('nin', 'Not provided')}")
                with col2:
                    st.write(f"**Role:** {user_data.get('role_name', 'Not defined')}")
                    status_text = "Active" if user_data['is_active'] == 1 else "Inactive"
                    st.write(f"**Status:** {status_text}")
                    st.write(f"**Created on:** {user_data.get('created_at', 'Not available')}")
            
            with st.form(f"edit_user_form_{selected_user_id}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Full name *", value=user_data['name'] or "")
                    new_email = st.text_input("Email *", value=user_data['email'] or "")
                    new_nin = st.text_input("NIN", value=user_data['nin'] or "")
                with col2:
                    role_options_edit = [role['name'] for role in roles] if roles else []
                    current_role_index = next((i for i, role in enumerate(roles) if role['name'] == user_data['role_name']), 0)
                    new_role = st.selectbox("Role *", role_options_edit, index=current_role_index)
                    new_status = st.selectbox("Status", ["Active", "Inactive"], index=0 if user_data['is_active'] == 1 else 1)
                    change_password = st.checkbox("Change password")
                    new_password = st.text_input("New password", type="password", placeholder="New secure password" if change_password else "Check 'Change password' to enable", disabled=not change_password)
                    confirm_new_password = st.text_input("Confirm new password", type="password", placeholder="Confirm new password" if change_password else "Check 'Change password' to enable", disabled=not change_password)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    update_submitted = st.form_submit_button("💾 Update", type="primary")
                with col2:
                    if st.form_submit_button("🔄 Reset"):
                        st.rerun()
                with col3:
                    if user_data['is_active'] == 1:
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
                                    user_id=selected_user_id,
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
                                        conn.execute("UPDATE user SET password = ? WHERE id = ?", (hashed_password, selected_user_id))
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
                    success, message = db_manager.update_user(selected_user_id, is_active=0, updated_by=st.session_state.get('user_id', 1))
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                
                if 'activate_submitted' in locals() and activate_submitted:
                    success, message = db_manager.update_user(selected_user_id, is_active=1, updated_by=st.session_state.get('user_id', 1))
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        else:
            st.error("❌ Unable to retrieve user data")

# Statistics Tab
if "📊 Statistics" in available_tabs:
    tab_index = available_tabs.index("📊 Statistics")
    with tabs[tab_index]:
        st.subheader("Statistics")
        try:
            stats = db_manager.get_user_stats()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Users", stats['total'])
            with col2:
                st.metric("Active", stats['active'])
            with col3:
                st.metric("Inactive", stats['inactive'])
            
            if stats['by_role']:
                df_stats = pd.DataFrame(stats['by_role'])
                st.subheader("Users by Role")
                st.dataframe(df_stats)
        except Exception as e:
            st.error(f"Error loading statistics: {str(e)}")
            st.info("Statistics feature to be implemented")