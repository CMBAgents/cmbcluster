import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from components.api_client import api_client

def show_storage_selector(user_storages: List[Dict] = None) -> Dict:
    """
    Display storage selection interface for environment creation
    
    Returns:
        Dict with storage selection information
    """
    if user_storages is None:
        try:
            response = api_client.list_user_storages()
            user_storages = response.get("storages", [])
        except Exception as e:
            st.error(f"Failed to load storage options: {str(e)}")
            user_storages = []
    
    st.markdown("### 💾 Workspace Storage Selection")
    
    # Check if user has existing storage
    active_storages = [s for s in user_storages if s.get("status") == "active"]
    
    if not active_storages:
        # First time user - auto-create storage
        st.info("🌟 **Welcome!** We'll create your first cosmic workspace automatically.")
        st.markdown("""
        Your workspace will be given a unique **cosmology-themed name** like:
        - *Andromeda Nebula* 🌌
        - *Orion Quasar* ⭐
        - *Vega Pulsar* 💫
        """)
        
        return {
            "selection_type": "create_new",
            "storage_id": None,
            "create_new": True
        }
    
    # Existing user - show options
    st.markdown("Choose your workspace storage:")
    
    # Storage selection options
    storage_option = st.radio(
        "Storage Options",
        ["continue_existing", "create_new"],
        format_func=lambda x: {
            "continue_existing": "🔄 Continue with existing workspace",
            "create_new": "✨ Start fresh with new workspace"
        }[x],
        index=0,
        key="storage_selection_radio"
    )
    
    selected_storage = None
    
    if storage_option == "continue_existing":
        # Show existing storage options
        st.markdown("#### 📂 Your Existing Workspaces")
        
        # Create a more detailed storage display
        for i, storage in enumerate(active_storages):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                display_name = storage.get("display_name", "Unknown Workspace")
                st.markdown(f"**{display_name}**")
                st.caption(f"Bucket: `{storage.get('bucket_name', 'unknown')}`")
            
            with col2:
                created_date = storage.get("created_at", "")
                if created_date:
                    try:
                        dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                        st.write(f"📅 {dt.strftime('%Y-%m-%d')}")
                    except:
                        st.write("📅 Unknown")
                else:
                    st.write("📅 Unknown")
            
            with col3:
                size_bytes = storage.get("size_bytes", 0)
                if size_bytes > 0:
                    size_str = format_storage_size(size_bytes)
                    st.write(f"📊 {size_str}")
                else:
                    st.write("📊 Empty")
            
            with col4:
                if st.button("Select", key=f"select_storage_{i}", type="primary"):
                    selected_storage = storage
                    st.session_state.selected_storage_id = storage["id"]
                    st.success(f"Selected: {display_name}")
        
        # If storage was selected via session state
        if "selected_storage_id" in st.session_state and not selected_storage:
            selected_storage_id = st.session_state.selected_storage_id
            selected_storage = next((s for s in active_storages if s["id"] == selected_storage_id), None)
        
        if selected_storage:
            # Show selected storage details
            st.markdown("---")
            st.markdown("#### ✅ Selected Workspace")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📛 Name", selected_storage.get("display_name", "Unknown"))
                st.metric("💽 Size", format_storage_size(selected_storage.get("size_bytes", 0)))
            with col2:
                st.metric("📁 Objects", selected_storage.get("object_count", 0))
                st.metric("🏷️ Class", selected_storage.get("storage_class", "Unknown"))
            
            return {
                "selection_type": "existing",
                "storage_id": selected_storage["id"],
                "storage_name": selected_storage.get("display_name"),
                "create_new": False
            }
        else:
            # No storage selected yet
            st.info("👆 Please select a workspace from above to continue.")
            return {"selection_type": "pending"}
    
    else:  # create_new
        st.markdown("#### ✨ Create New Workspace")
        st.info("🎲 A new cosmology-themed workspace will be created automatically!")
        
        # Storage class selection
        storage_class = st.selectbox(
            "Storage Performance",
            ["STANDARD", "NEARLINE", "COLDLINE"],
            format_func=lambda x: {
                "STANDARD": "🚀 Standard (Best performance)",
                "NEARLINE": "⚡ Nearline (Good for monthly access)", 
                "COLDLINE": "❄️ Coldline (Archive storage)"
            }[x],
            index=0,
            help="Choose storage class based on how frequently you'll access your data"
        )
        
        st.markdown("**New workspace features:**")
        st.markdown("- 🌌 Unique cosmic name (e.g., 'Sirius Galaxy')")
        st.markdown("- 🔒 Private and secure")
        st.markdown("- 📈 Automatic versioning enabled")
        st.markdown("- ♻️ Lifecycle management")
        
        return {
            "selection_type": "create_new",
            "storage_id": None,
            "create_new": True,
            "storage_class": storage_class
        }

def format_storage_size(size_bytes: int) -> str:
    """Format storage size in human-readable format"""
    if size_bytes == 0:
        return "Empty"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def show_storage_creation_status(storage_info: Dict):
    """Show storage creation progress and status"""
    if storage_info.get("selection_type") == "create_new":
        with st.spinner("🌌 Creating your cosmic workspace..."):
            st.info("✨ Generating unique cosmology-themed name...")
            st.info("🏗️ Setting up secure cloud storage...")
            st.info("🔐 Configuring permissions...")

def clear_storage_selection():
    """Clear storage selection from session state"""
    keys_to_clear = [
        "selected_storage_id",
        "storage_selection_radio"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
