import streamlit as st
from services.tickets.data_loader import load_deletable_tickets
from database import db_manager
from services.cache_utils import clear_cache
from permissions import PermissionManager

def display():
    st.header("Delete a Ticket")
    st.error(
        "🚨 **DANGER**: This action will **PERMANENTLY DELETE** the ticket from the database. This action is **IRREVERSIBLE**!"
    )
    st.warning(
        "⚠️ Please make sure you have backed up any important data before proceeding."
    )

    # Récupérer les tickets que l'utilisateur peut supprimer
    tickets = load_deletable_tickets()
    
    # Afficher les règles de suppression selon le rôle
    current_user_id = PermissionManager.get_user_id()
    if current_user_id:
        user_roles = db_manager.get_user_roles(current_user_id)
        user_role_names = [role['name'] for role in user_roles]
        
        if 'admin' in user_role_names:
            st.info("🔑 **Admin**: You can delete any ticket in the system.")
        elif 'manager' in user_role_names:
            st.info("👥 **Manager**: You can delete tickets created by your team members.")
        elif 'agent' in user_role_names:
            st.info("👤 **Agent**: You can only delete tickets you created.")

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

                # Enhanced confirmation process
                st.markdown("---")
                st.markdown("### ⚠️ Confirmation Required")
                
                # Checkbox confirmation
                confirm_understanding = st.checkbox(
                    "I understand that this action will permanently delete the ticket and cannot be undone",
                    key=f"confirm_understanding_{ticket_id}"
                )
                
                # Text confirmation
                confirm_text = st.text_input(
                    "Type 'DELETE' to confirm permanent deletion:",
                    key=f"confirm_text_{ticket_id}",
                    disabled=not confirm_understanding
                )

                # Deletion confirmation
                col1, col2, col3 = st.columns([1, 1, 2])

                with col1:
                    if st.button(
                        "🗑️ PERMANENTLY DELETE", 
                        type="primary", 
                        key="confirm_delete",
                        disabled=not (confirm_understanding and confirm_text.upper() == "DELETE")
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
        
        # Afficher un message explicatif selon le rôle
        current_user_id = PermissionManager.get_user_id()
        if current_user_id:
            user_roles = db_manager.get_user_roles(current_user_id)
            user_role_names = [role['name'] for role in user_roles]
            
            if 'agent' in user_role_names:
                st.info("💡 **Note**: As an agent, you can only delete tickets you created.")
            elif 'manager' in user_role_names:
                st.info("💡 **Note**: As a manager, you can only delete tickets created by your team members.")
            else:
                st.info("💡 **Note**: No tickets are available for deletion.")
