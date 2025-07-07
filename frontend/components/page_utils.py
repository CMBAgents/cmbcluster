"""
Page utilities for preventing content stacking in multi-page Streamlit apps
"""
import streamlit as st

def clear_page():
    """
    Clear the current page to prevent content stacking when navigating between pages.
    This function ensures that only the current page's content is displayed.
    """
    # Clear any existing containers
    if hasattr(st.session_state, 'page_containers'):
        for container in st.session_state.page_containers:
            try:
                container.empty()
            except:
                pass
    
    # Reset page containers list
    st.session_state.page_containers = []
    
    # Use st.empty to clear the main content area
    main_container = st.empty()
    st.session_state.page_containers.append(main_container)
    
    return main_container

def init_page(title, subtitle=None):
    """
    Initialize a page with proper clearing and setup.
    
    Args:
        title: Page title
        subtitle: Optional subtitle
    
    Returns:
        Main container for the page content
    """
    # Clear previous page content
    container = clear_page()
    
    # Set up the page content in the cleared container
    with container.container():
        st.markdown(f"# {title}")
        if subtitle:
            st.markdown(subtitle)
    
    return container
