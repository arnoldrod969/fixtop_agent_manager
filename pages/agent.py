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
if not PermissionManager.check_page_access('agent_page'):
    PermissionManager.show_access_denied("You do not have the necessary permissions to access this page.")

"""Agent management page"""
st.title("🤖 Agent Management")

# Define data loading functions
def load_agents_data():
    """Load agents data from database"""
    try:
        # Get all users with "agent" role
        users = db_manager.get_all_users()
        if users:
            df = pd.DataFrame(users)
            # Filter only agents
            agents_df = df[df['role_name'] == 'agent'].copy()
            # Convert dates
            if 'created_at' in agents_df.columns:
                agents_df['created_at'] = pd.to_datetime(agents_df['created_at'])
            if 'updated_at' in agents_df.columns:
                agents_df['updated_at'] = pd.to_datetime(agents_df['updated_at'])
            return agents_df
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['id', 'nin', 'name', 'email', 'role_name', 'is_active', 'created_at'])
    except Exception as e:
        st.error(f"Error loading agents: {str(e)}")
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
available_tabs = PermissionManager.get_available_tabs('agent_page')

if not available_tabs:
    st.error("No tabs available for your role.")
    st.stop()

# Create tabs dynamically
tabs = st.tabs(available_tabs)

# Load roles globally for reuse
roles = load_roles_data()

# List Tab (equivalent to Consulter)
if "📋 List" in available_tabs:
    tab_index = available_tabs.index("📋 List")
    with tabs[tab_index]:
        st.subheader("📋 Agent List")
        
        # Load data
        agents_df = load_agents_data()
        
        if not agents_df.empty:
            # In List tab, all users can see all agents (read-only)
            # Permission filtering applies only to Edit tab
            
            
            # Filters
            col1, col2 = st.columns(2)
            
            with col1:
                status_filter = st.selectbox(
                    "Filter by status",
                    ["All", "Active", "Inactive"]
                )
            
            with col2:
                search_term = st.text_input("Search by name or email", placeholder="Type to search...")
            
            # Apply filters
            filtered_df = agents_df.copy()
            
            if status_filter == "Active":
                filtered_df = filtered_df[filtered_df['is_active'] == 1]
            elif status_filter == "Inactive":
                filtered_df = filtered_df[filtered_df['is_active'] == 0]
            
            if search_term.strip():
                search_lower = search_term.lower()
                filtered_df = filtered_df[
                    filtered_df['name'].str.lower().str.contains(search_lower, na=False) |
                    filtered_df['email'].str.lower().str.contains(search_lower, na=False)
                ]
            
            # Prepare display DataFrame
            display_df = filtered_df.copy()
            if not display_df.empty:
                display_df['Status'] = display_df['is_active'].apply(lambda x: "Active" if x == 1 else "Inactive")
                display_df = display_df[['id', 'nin', 'name', 'email', 'role_name', 'Status', 'created_at']]
                display_df.columns = ['ID', 'NIN', 'Name', 'Email', 'Role', 'Status', 'Creation Date']
                display_df = display_df.reset_index(drop=True)
            
            # Display data
            if not display_df.empty:
                st.dataframe(display_df, use_container_width=True, height=400)
            else:
                st.info("No agents found with the selected filters.")
        else:
            st.info("No agents available.")

# Add Tab
if "➕ Add" in available_tabs:
    tab_index = available_tabs.index("➕ Add")
    with tabs[tab_index]:
        st.subheader("Add an Agent")
        with st.form("add_agent_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full name *", placeholder="Ex: John Doe")
                email = st.text_input("Email *", placeholder="john.doe@fixtop.com")
                nin = st.text_input("NIN", placeholder="Identification number (optional)")
            with col2:
                # Only agent role available
                role_options_add = ["agent"]
                selected_role = st.selectbox("Role *", role_options_add)
                password = st.text_input("Password *", type="password", placeholder="Secure password")
                confirm_password = st.text_input("Confirm password *", type="password", placeholder="Confirm password")
            
            submitted = st.form_submit_button("Create agent")
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
                    # Validate password strength
                    is_strong, errors = db_manager.validate_password_strength(password)
                    if not is_strong:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        # Get role_id from selected_role
                        role_id = next((role['id'] for role in roles if role['name'] == selected_role), None)
                        if not role_id:
                            st.error("❌ Invalid role")
                        else:
                            created_by = st.session_state.get('user_id', 1)  # Connected user ID
                            # Create user
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
        st.subheader("Edit an Agent")
        agents_df = load_agents_data()
        if not agents_df.empty:
            # Filter agents according to permissions
            current_user_role = PermissionManager.get_user_role()
            current_user_id = PermissionManager.get_user_id()
            
            # If the user is an agent, they can only edit their own information
            if current_user_role == 'agent' and not PermissionManager.has_permission('agent_page', 'can_view_all'):
                if current_user_id:
                    agents_df = agents_df[agents_df['id'] == current_user_id]
                else:
                    st.error("❌ Unable to identify your user profile.")
                    st.stop()
            
            if agents_df.empty:
                st.warning("No agents available for editing.")
                st.stop()
            
            # Create options for the selectbox
            agent_options = agents_df.apply(lambda x: f"{x['name']} ({x['email']}) - ID={x['id']}", axis=1).tolist()
            
            # If only one agent (case of agent editing their own info), display an informative message
            if len(agent_options) == 1:
                st.info(f"📝 Editing your profile: {agent_options[0]}")
                selected_option = agent_options[0]
            else:
                selected_option = st.selectbox("Choose an agent", agent_options)
            
            selected_agent_id = int(selected_option.split("ID=")[-1])
            
            # Additional permission check for editing
            if not PermissionManager.can_edit_user(selected_agent_id, 'agent'):
                st.error("❌ You do not have permissions to edit this agent.")
                st.info("💡 You can only edit your own information.")
                st.stop()
            
            agent_data = agents_df[agents_df['id'] == selected_agent_id].iloc[0]
            
            # Display current information
            with st.expander("📋 Current information", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Name:** {agent_data['name']}")
                    st.write(f"**Email:** {agent_data['email']}")
                    st.write(f"**NIN:** {agent_data.get('nin', 'Not provided')}")
                with col2:
                    st.write(f"**Role:** {agent_data.get('role_name', 'Not defined')}")
                    status_text = "Active" if agent_data['is_active'] == 1 else "Inactive"
                    st.write(f"**Status:** {status_text}")
                    st.write(f"**Created on:** {agent_data.get('created_at', 'Not available')}")
            
            with st.form(f"edit_agent_form_{selected_agent_id}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Full name *", value=agent_data['name'] or "")
                    new_email = st.text_input("Email *", value=agent_data['email'] or "")
                    new_nin = st.text_input("NIN", value=agent_data['nin'] or "")
                with col2:
                    # Limit role options to "agent" only
                    role_options_edit = ["agent"]
                    current_role_index = 0  # Always 0 since there's only one option
                    new_role = st.selectbox("Role *", role_options_edit, index=current_role_index)
                    new_status = st.selectbox("Status", ["Active", "Inactive"], index=0 if agent_data['is_active'] == 1 else 1)
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
                    if agent_data['is_active'] == 1:
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
                                    user_id=selected_agent_id,
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
                                        conn.execute("UPDATE user SET password = ? WHERE id = ?", (hashed_password, selected_agent_id))
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
                    success, message = db_manager.update_user(selected_agent_id, is_active=0, updated_by=st.session_state.get('user_id', 1))
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                
                if 'activate_submitted' in locals() and activate_submitted:
                    success, message = db_manager.update_user(selected_agent_id, is_active=1, updated_by=st.session_state.get('user_id', 1))
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        else:
            st.error("❌ Unable to retrieve agent data")

# Delete Tab
if "🗑️ Delete" in available_tabs:
    tab_index = available_tabs.index("🗑️ Delete")
    with tabs[tab_index]:
        st.header("🗑️ Delete an agent")
        st.warning("⚠️ **Warning:** Deleting an agent is irreversible!")
        
        # Load agent data
        agents_df = load_agents_data()
        
        if agents_df.empty:
            st.info("No agents available for deletion.")
        else:
            # Agent selector
            st.subheader("🎯 Select the agent to delete")
            
            # Create a list of options with name and email
            agent_options = {}
            for _, agent in agents_df.iterrows():
                display_name = f"{agent['name']} ({agent['email']}) - ID: {agent['id']}"
                agent_options[display_name] = agent['id']
            
            selected_agent_display = st.selectbox(
                "Choose an agent to delete",
                [""] + list(agent_options.keys()),
                help="Select the agent you want to delete"
            )
            
            if selected_agent_display:
                selected_agent_id = agent_options[selected_agent_display]
                
                # Retrieve complete data of the selected agent
                try:
                    agent_data = db_manager.get_user_by_id(selected_agent_id)
                    
                    if agent_data:
                        # Display information of the agent to be deleted
                        st.error(f"🎯 **Agent selected for deletion:** {agent_data['name']}")
                        
                        with st.expander("📋 Agent information", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Name:** {agent_data['name']}")
                                st.write(f"**Email:** {agent_data['email']}")
                                st.write(f"**NIN:** {agent_data.get('nin', 'Not provided')}")
                            with col2:
                                st.write(f"**Role:** {agent_data.get('role_name', 'Not defined')}")
                                status_text = "Active" if agent_data['is_active'] == 1 else "Inactive"
                                st.write(f"**Status:** {status_text}")
                                st.write(f"**Created on:** {agent_data.get('created_at', 'Not available')}")
                        
                        # Deletion confirmation
                        st.subheader("⚠️ Deletion confirmation")
                        
                        confirmation_text = st.text_input(
                            f"To confirm deletion, type the agent's name: **{agent_data['name']}**",
                            placeholder=f"Type exactly: {agent_data['name']}"
                        )
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("🗑️ Confirm deletion", type="primary", disabled=(confirmation_text != agent_data['name'])):
                                try:
                                    success, message = db_manager.delete_user(selected_agent_id)
                                    
                                    if success:
                                        st.success(f"✅ {message}")
                                        st.balloons()
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                                        
                                except Exception as e:
                                    st.error(f"❌ Unexpected error: {str(e)}")
                        
                        with col2:
                            if st.button("❌ Cancel"):
                                st.rerun()
                        
                        if confirmation_text != agent_data['name'] and confirmation_text:
                            st.error("The entered name does not match. Please type exactly the agent's name.")
                    else:
                        st.error("Agent not found in database.")
                        
                except Exception as e:
                    st.error(f"Error retrieving agent data: {str(e)}")

# Statistics Tab
if "📊 Statistics" in available_tabs:
    tab_index = available_tabs.index("📊 Statistics")
    with tabs[tab_index]:
        st.subheader("Agent Statistics")
        try:
            stats = db_manager.get_user_stats()
            # Load data
            agents_df = load_agents_data()
            # Filter for agents if necessary
            agent_stats = {k: v for k, v in stats.items() if k != 'by_role'}
            agent_by_role = [r for r in stats['by_role'] if r['name'] == 'agent']
            agent_stats['by_role'] = agent_by_role if agent_by_role else [{'name': 'agent', 'count': 0}]
            
            # Display statistics
            colx1, colx2, colx3, colx4 = st.columns(4)
            
            with colx1:
                total_agents = len(agents_df)
                st.metric("Total Agents", total_agents)
            
            with colx2:
                active_agents = len(agents_df[agents_df['is_active'] == 1])
                st.metric("Active Agents", active_agents)
            
            with colx3:
                inactive_agents = len(agents_df[agents_df['is_active'] == 0])
                st.metric("Inactive Agents", inactive_agents)
            
            with colx4:
                if not agents_df.empty and 'created_at' in agents_df.columns:
                    recent_agents = len(agents_df[agents_df['created_at'] >= datetime.now() - timedelta(days=30)])
                    st.metric("New (30d)", recent_agents)
                else:
                    st.metric("New (30d)", 0)
            
            if agent_stats['by_role']:
                df_stats = pd.DataFrame(agent_stats['by_role'])
                st.subheader("Agents by Role")
                st.dataframe(df_stats)
        except Exception as e:
            st.error(f"Error loading statistics: {str(e)}")
            st.info("Statistics feature to be implemented")