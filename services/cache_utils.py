import streamlit as st

def clear_cache():
    """Clear Streamlit cache (used throughout the app)."""
    try:
        st.cache_data.clear()
    except Exception:
        # Fallback if st.cache_data API changes
        try:
            st.legacy_caching.caching.clear_cache()
        except Exception:
            pass
