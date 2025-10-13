import streamlit as st

def show_sidebar():
    with st.sidebar:
        if hasattr(st.session_state, 'user_name'):
            st.markdown(f"**Logged in as:** {st.session_state.user_name}")
            st.markdown(f"**Email:** {st.session_state.username}")
            st.markdown(f"**Role:** {st.session_state.user_role}")
        else:
            st.markdown(f"**Logged in as:** {st.session_state.username}")
            st.markdown(f"**Role:** Administrator")

        st.markdown("---")
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
