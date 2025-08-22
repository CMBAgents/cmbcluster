import streamlit as st
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

# Configure Streamlit's max upload size to 1MB
try:
    # Set the max upload size to 1MB (1 * 1024 * 1024 bytes)
    st._config.set_option('server.maxUploadSize', 1)
except:
    # Fallback if the above doesn't work in this Streamlit version
    pass

logger = structlog.get_logger()

class FileUploadManager:
    """Manages file upload UI and operations"""
    
    def __init__(self, api_client, debug_mode=False):
        self.api_client = api_client
        self.debug_mode = debug_mode
    
    def show_file_upload_section(self):
        """Display the complete file upload section"""
        st.markdown("""
        <div class="settings-section">
            <h3>Environment Files</h3>
            <p>Upload JSON configuration files that will be securely stored and made available in your research environments.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show debug panel if debug mode is enabled
        if self.debug_mode:
            self._show_debug_panel()
        
        # Show existing files first
        self._show_existing_files()
        
        st.markdown("---")
        
        # File upload interface
        self._show_file_upload_interface()
    
    def _show_debug_panel(self):
        """Show debug information for API connectivity"""
        st.markdown("### 🔧 Debug Information")
        
        with st.expander("API Connection Test", expanded=False):
            if st.button("Test API Connection"):
                try:
                    # Test basic API connectivity
                    base_url = getattr(self.api_client, 'base_url', 'Not available')
                    st.write(f"**API Base URL:** {base_url}")
                    
                    # Test authentication
                    headers = getattr(self.api_client, '_get_headers', lambda: {})()
                    st.write(f"**Authentication Headers:** {'✅ Present' if headers else '❌ Missing'}")
                    
                    # Test file API endpoint
                    try:
                        response = self.api_client.list_user_files()
                        st.write(f"**API Response Type:** {type(response)}")
                        st.write(f"**API Response:** {response}")
                        
                        if isinstance(response, dict) and response.get("status") == "error":
                            st.error(f"API Error: {response.get('message')}")
                        else:
                            st.success("API connection successful!")
                            
                    except Exception as e:
                        st.error(f"API Connection Failed: {str(e)}")
                        
                except Exception as e:
                    st.error(f"Debug test failed: {str(e)}")
        
        st.markdown("---")
    
    def _show_existing_files(self):
        """Display existing uploaded files"""
        st.markdown("### Your Uploaded Files")
        
        # Fetch existing files
        try:
            response = self.api_client.list_user_files()
            
            # Handle different response formats
            if isinstance(response, dict):
                if response.get("status") == "error":
                    st.markdown("""
                    <div class="file-validation-warning">
                        <span style="font-size: 1.2rem;">⚠️</span>
                        <div>
                            <strong>Unable to load files</strong><br>
                            There was an issue connecting to the server. Please check your connection and try refreshing the page.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    return
                else:
                    # Response might contain a 'files' key or similar
                    files = response.get("files", response.get("data", []))
            elif isinstance(response, list):
                files = response
            else:
                files = []
            
        except Exception as e:
            logger.error("Error loading user files", error=str(e))
            
            # Show user-friendly error message instead of raw exception
            st.markdown("""
            <div class="file-validation-warning">
                <span style="font-size: 1.2rem;">⚠️</span>
                <div>
                    <strong>Connection Error</strong><br>
                    Unable to connect to the server. Please check your internet connection and try again.
                </div>
            </div>
            """, unsafe_allow_html=True)
            files = []
        
        if not files:
            # Show beautiful empty state instead of error
            st.markdown("""
            <div class="file-empty-state">
                <div class="file-empty-state-icon">📁</div>
                <div class="file-empty-state-title">No Files Uploaded Yet</div>
                <div class="file-empty-state-text">
                    Upload your first JSON configuration file to get started.<br>
                    Files will be securely stored and automatically made available in your research environments.
                </div>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Display files in cards
        for file_info in files:
            self._show_file_card(file_info)
    
    def _show_file_card(self, file_info: Dict[str, Any]):
        """Display a single file card"""
        file_id = file_info.get("id")
        file_name = file_info.get("file_name", "Unknown")
        file_type = file_info.get("file_type", "unknown")
        env_var = file_info.get("environment_variable_name", "")
        container_path = file_info.get("container_path", "")
        file_size = file_info.get("file_size", 0)
        created_at = file_info.get("created_at", "")
        
        # File type display
        type_display = {
            "gcp_service_account": "🔑 GCP Service Account",
            "custom_json": "📄 Custom JSON File"
        }.get(file_type, f"📄 {file_type}")
        
        # Format file size
        size_display = self._format_file_size(file_size)
        
        # Format date
        date_display = self._format_date(created_at)
        
        with st.container():
            # File header
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{file_name}**")
                st.caption(f"{type_display} • {size_display} • {date_display}")
            
            with col2:
                # File actions
                action_col1, action_col2 = st.columns(2)
                
                with action_col1:
                    if st.button("✏️", key=f"edit_{file_id}", help="Edit file"):
                        st.session_state[f"edit_file_{file_id}"] = True
                        st.rerun()
                
                with action_col2:
                    if st.button("🗑️", key=f"delete_{file_id}", help="Delete file"):
                        st.session_state[f"confirm_delete_{file_id}"] = True
                        st.rerun()
            
            # File details
            detail_col1, detail_col2 = st.columns(2)
            
            with detail_col1:
                st.markdown("**Environment Variable:**")
                st.code(env_var)
            
            with detail_col2:
                st.markdown("**Container Path:**")
                st.code(container_path)
            
            # Show edit form if requested
            if st.session_state.get(f"edit_file_{file_id}", False):
                self._show_edit_file_form(file_info)
            
            # Show delete confirmation if requested
            if st.session_state.get(f"confirm_delete_{file_id}", False):
                self._show_delete_confirmation(file_info)
            
            st.markdown("---")
    
    def _show_edit_file_form(self, file_info: Dict[str, Any]):
        """Show file editing form"""
        file_id = file_info.get("id")
        
        st.markdown("#### Edit File Configuration")
        
        with st.form(f"edit_file_form_{file_id}"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input(
                    "File Name",
                    value=file_info.get("file_name", ""),
                    help="Display name for this file"
                )
                
                new_env_var = st.text_input(
                    "Environment Variable",
                    value=file_info.get("environment_variable_name", ""),
                    help="Environment variable name in containers"
                )
            
            with col2:
                new_path = st.text_input(
                    "Container Path",
                    value=file_info.get("container_path", ""),
                    help="Full path where file will be mounted in container"
                )
            
            # Form buttons
            submit_col1, submit_col2, submit_col3 = st.columns([1, 1, 1])
            
            with submit_col1:
                submitted = st.form_submit_button("💾 Save Changes", type="primary")
            
            with submit_col2:
                if st.form_submit_button("📄 Replace File"):
                    # Show file replacement interface
                    st.session_state[f"replace_file_{file_id}"] = True
                    st.rerun()
            
            with submit_col3:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state[f"edit_file_{file_id}"] = False
                    st.rerun()
            
            if submitted:
                self._update_file(file_id, new_name, new_env_var, new_path)
        
        # Show file replacement interface if requested
        if st.session_state.get(f"replace_file_{file_id}", False):
            self._show_file_replacement(file_info)
    
    def _show_file_replacement(self, file_info: Dict[str, Any]):
        """Show file content replacement interface"""
        file_id = file_info.get("id")
        
        st.markdown("#### Replace File Content")
        
        uploaded_file = st.file_uploader(
            "Choose replacement file",
            type=['json'],
            key=f"replace_upload_{file_id}",
            help="Upload a new JSON file to replace the current content"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Replace Content", key=f"do_replace_{file_id}", type="primary", disabled=not uploaded_file):
                if uploaded_file:
                    self._replace_file_content(file_id, uploaded_file)
        
        with col2:
            if st.button("❌ Cancel Replace", key=f"cancel_replace_{file_id}"):
                st.session_state[f"replace_file_{file_id}"] = False
                st.rerun()
    
    def _show_delete_confirmation(self, file_info: Dict[str, Any]):
        """Show delete confirmation dialog"""
        file_id = file_info.get("id")
        file_name = file_info.get("file_name", "")
        
        st.warning(f"Are you sure you want to delete **{file_name}**? This action cannot be undone.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Yes, Delete", key=f"confirm_delete_yes_{file_id}", type="primary"):
                self._delete_file(file_id, file_name)
        
        with col2:
            if st.button("❌ Cancel", key=f"confirm_delete_no_{file_id}"):
                st.session_state[f"confirm_delete_{file_id}"] = False
                st.rerun()
    
    def _show_file_upload_interface(self):
        """Display the file upload interface"""
        st.markdown("### Upload New File")
        
        # Show size limit warning prominently
        st.info("📋 **File Size Limit**: Maximum file size is **1MB**. Larger files will be rejected.")
        
        # File upload with custom size limit
        uploaded_file = st.file_uploader(
            "Choose a JSON file",
            type=['json'],
            help="Upload JSON configuration files",
            key="new_file_upload",
            # Set Streamlit's upload limit to match our validation (1MB)
            accept_multiple_files=False
        )
        
        if uploaded_file is not None:
            # Validate file size
            if uploaded_file.size > 1024 * 1024:  # 1MB limit
                st.error(f"❌ **File too large**: {self._format_file_size(uploaded_file.size)} exceeds the 1MB limit")
                st.info("💡 **Tip**: Try compressing your JSON file or removing unnecessary whitespace and comments to reduce file size.")
                return
            
            # Read and validate JSON content
            try:
                content = uploaded_file.read()
                json_content = json.loads(content.decode('utf-8'))
                st.success("✅ Valid JSON file uploaded")
                
                # Show file preview
                with st.expander("📋 File Preview", expanded=False):
                    st.json(json_content)
                
                # File configuration form
                self._show_file_configuration_form(uploaded_file, content, json_content)
                
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON file: {str(e)}")
                st.info("💡 **Tip**: Please check your JSON syntax. Common issues include missing commas, unmatched brackets, or unquoted strings.")
                
                # Show the problematic content if it's small enough
                if len(content) < 1000:
                    with st.expander("📄 File Content (for debugging)", expanded=False):
                        st.code(content.decode('utf-8', errors='replace'))
                        
            except UnicodeDecodeError as e:
                st.error(f"File encoding error: {str(e)}")
                st.info("💡 **Tip**: Please ensure your file is saved in UTF-8 encoding.")
                
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                st.info("💡 **Tip**: Please check that your file is not corrupted and is accessible.")
    
    def _show_file_configuration_form(self, uploaded_file, content: bytes, json_content: dict):
        """Show file configuration options"""
        st.markdown("#### File Configuration")
        
        # Auto-detect GCP service account
        is_gcp_key = self._detect_gcp_service_account(json_content)
        
        # Get file type selection outside the form to detect changes
        file_type = st.selectbox(
            "File Type",
            options=["custom_json", "gcp_service_account"],  # Put custom_json first as default
            format_func=lambda x: {
                "gcp_service_account": "🔑 GCP Service Account Key",
                "custom_json": "📄 Custom JSON File"
            }.get(x, x),
            help="Select the type of file you're uploading",
            key=f"file_type_{uploaded_file.name.replace('.', '_').replace(' ', '_')}"
        )
        
        # Show auto-detection hint
        if is_gcp_key and file_type == "custom_json":
            st.info("🔍 This looks like a GCP service account key. Consider selecting that file type.")
        
        # Create form with container to properly capture form state
        form_container = st.container()
        
        with form_container:
            # Create a unique form key based on filename AND file type to reset form when type changes
            form_key = f"file_config_form_{uploaded_file.name.replace('.', '_').replace(' ', '_')}_{file_type}"
            
            with st.form(form_key, clear_on_submit=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Environment variable name - conditional logic based on file type from outside form
                    if file_type == "gcp_service_account":
                        env_var_name = st.text_input(
                            "Environment Variable Name",
                            value="GOOGLE_APPLICATION_CREDENTIALS",
                            disabled=True,
                            key=f"env_var_gcp_{file_type}",
                            help="Standard environment variable for GCP service accounts"
                        )
                    else:
                        env_var_name = st.text_input(
                            "Environment Variable Name",
                            value="",
                            disabled=False,  # Explicitly set to False for custom files
                            key=f"env_var_custom_{file_type}",
                            placeholder="e.g., CONFIG_FILE, API_CREDENTIALS",
                            help="Name of environment variable that will point to this file (required)"
                        )
                
                with col2:
                    # Container path - conditional logic based on file type from outside form
                    if file_type == "gcp_service_account":
                        container_path = st.text_input(
                            "Container Path",
                            value="/app/secrets/gcp_service_account.json",
                            disabled=True,
                            key=f"container_path_gcp_{file_type}",
                            help="Path where file will be mounted in container (editable)"
                        )
                    else:
                        # Auto-generate path for custom JSON files
                        auto_generated_path = f"/mnt/user-files/{uploaded_file.name}"
                        container_path = st.text_input(
                            "Container Path",
                            value=auto_generated_path,
                            disabled=True,
                            key=f"container_path_custom_{file_type}",
                            help="Auto-generated path where file will be mounted in container"
                        )
                    
                    # File size info
                    st.markdown("**File Information:**")
                    st.write(f"• **Size:** {self._format_file_size(len(content))}")
                    st.write(f"• **Name:** {uploaded_file.name}")
                    
                    if is_gcp_key:
                        project_id = json_content.get("project_id", "Unknown")
                        st.write(f"• **GCP Project:** {project_id}")
                
                # Form submission button (no validation here, always enabled)
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    submitted = st.form_submit_button(
                        "🚀 Upload File",
                        type="primary",
                        use_container_width=True
                    )
            
            # Validation happens AFTER form submission (outside the form)
            if submitted:
                valid_config = True
                validation_errors = []
                
                # Environment variable validation - required for all file types
                if not env_var_name or not env_var_name.strip():
                    validation_errors.append("Environment variable name is required")
                    valid_config = False
                else:
                    # Check for duplicate environment variable names
                    try:
                        existing_files_response = self.api_client.list_user_files()
                        existing_files = existing_files_response if isinstance(existing_files_response, list) else []
                        
                        existing_env_vars = [f.get('environment_variable_name') for f in existing_files if f.get('environment_variable_name')]
                        
                        if env_var_name.strip() in existing_env_vars:
                            validation_errors.append(f"Environment variable '{env_var_name.strip()}' is already used by another file")
                            valid_config = False
                            
                    except Exception as e:
                        # Don't fail upload if we can't check duplicates, let backend handle it
                        pass
                
                # Container path validation
                if not container_path or not container_path.strip():
                    validation_errors.append("Container path is required")
                    valid_config = False
                
                # GCP service account specific validation
                if file_type == "gcp_service_account" and not is_gcp_key:
                    validation_errors.append("Selected GCP service account but file doesn't appear to be a valid service account key")
                    valid_config = False
                
                # Handle validation results
                if valid_config:
                    # Proceed with upload
                    self._upload_file(content, uploaded_file.name, file_type, env_var_name.strip(), container_path)
                else:
                    # Show validation errors
                    st.error("❌ **Upload failed due to validation errors:**")
                    for error in validation_errors:
                        st.error(f"• {error}")
                    
                    # Show helpful suggestions
                    if any("Environment variable" in error and "already used" in error for error in validation_errors):
                        st.info("💡 **Suggestion**: Try using a different name like 'CONFIG_FILE_2', 'API_KEY_DEV', or add a suffix to make it unique.")
                    
                    st.info("ℹ️ Please correct the errors above and try uploading again.")
    
    def _detect_gcp_service_account(self, json_content: dict) -> bool:
        """Detect if JSON content is a GCP service account key"""
        required_fields = ["type", "project_id", "private_key", "client_email"]
        return (
            json_content.get("type") == "service_account" and
            all(field in json_content for field in required_fields)
        )
    
    def _upload_file(self, content: bytes, filename: str, file_type: str, env_var_name: Optional[str], container_path: str):
        """Upload file to backend"""
        try:
            with st.spinner("Uploading file..."):
                response = self.api_client.upload_user_file(
                    file_data=content,
                    filename=filename,
                    file_type=file_type,
                    env_var_name=env_var_name,
                    container_path=container_path
                )
            
            if response.get("status") == "error":
                error_msg = response.get('message', 'Unknown error')
                st.error(f"Upload failed: {error_msg}")
                
                # Provide specific help based on error type
                if "Environment variable" in error_msg and "already used" in error_msg:
                    st.info("💡 **Tip**: Each file must have a unique environment variable name. Try using a different name like 'CONFIG_FILE_2' or 'API_CREDENTIALS_DEV'.")
                elif "Invalid JSON" in error_msg or "JSON" in error_msg:
                    st.info("💡 **Tip**: Please ensure your file contains valid JSON format. You can use online JSON validators to check your file.")
                elif "GCP service account" in error_msg:
                    st.info("💡 **Tip**: If this is a GCP service account key, ensure it contains all required fields (type, project_id, private_key, client_email, etc.)")
                elif "required" in error_msg.lower():
                    st.info("💡 **Tip**: Make sure all required fields are filled out, especially the environment variable name.")
                
            else:
                st.success("✅ File uploaded successfully!")
                st.balloons()
                
                # Clear upload state
                if "new_file_upload" in st.session_state:
                    del st.session_state["new_file_upload"]
                
                # Refresh page to show new file
                st.rerun()
                
        except Exception as e:
            st.error(f"Error uploading file: {str(e)}")
    
    def _update_file(self, file_id: str, new_name: str, new_env_var: str, new_path: str):
        """Update file metadata"""
        try:
            updates = {}
            if new_name:
                updates["file_name"] = new_name
            if new_env_var:
                updates["environment_variable_name"] = new_env_var
            if new_path:
                updates["container_path"] = new_path
            
            if not updates:
                st.warning("No changes to save")
                return
            
            with st.spinner("Updating file..."):
                response = self.api_client.update_user_file(file_id, **updates)
            
            if response.get("status") == "error":
                st.error(f"Update failed: {response.get('message', 'Unknown error')}")
            else:
                st.success("✅ File updated successfully!")
                st.session_state[f"edit_file_{file_id}"] = False
                st.rerun()
                
        except Exception as e:
            st.error(f"Error updating file: {str(e)}")
    
    def _replace_file_content(self, file_id: str, uploaded_file):
        """Replace file content"""
        try:
            # Read and validate new content
            content = uploaded_file.read()
            json.loads(content.decode('utf-8'))  # Validate JSON
            
            with st.spinner("Replacing file content..."):
                response = self.api_client.update_user_file(
                    file_id, 
                    content=content.decode('utf-8'),
                    file_size=len(content)
                )
            
            if response.get("status") == "error":
                st.error(f"Replace failed: {response.get('message', 'Unknown error')}")
            else:
                st.success("✅ File content replaced successfully!")
                st.session_state[f"replace_file_{file_id}"] = False
                st.session_state[f"edit_file_{file_id}"] = False
                st.rerun()
                
        except json.JSONDecodeError:
            st.error("Replacement file must contain valid JSON")
        except Exception as e:
            st.error(f"Error replacing file: {str(e)}")
    
    def _delete_file(self, file_id: str, file_name: str):
        """Delete a file"""
        try:
            with st.spinner("Deleting file..."):
                response = self.api_client.delete_user_file(file_id)
            
            if response.get("status") == "error":
                st.error(f"Delete failed: {response.get('message', 'Unknown error')}")
            else:
                st.success(f"✅ File '{file_name}' deleted successfully!")
                st.session_state[f"confirm_delete_{file_id}"] = False
                st.rerun()
                
        except Exception as e:
            st.error(f"Error deleting file: {str(e)}")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} GB"
    
    def _format_date(self, date_string: str) -> str:
        """Format date string for display"""
        if not date_string:
            return "Unknown"
        
        try:
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return date_string
