import streamlit as st
import requests
import json
from typing import Dict, List, Optional
import os
from datetime import datetime
import structlog

logger = structlog.get_logger()

class StorageFileManager:
    """Manages file operations for storage buckets"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def show_file_browser(self, storage_id: str, storage_name: str):
        """Display file browser interface for a storage bucket"""
        st.subheader(f"📁 Files in {storage_name}")
        
        # Create columns for actions
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Path/prefix input
            prefix = st.text_input("📂 Folder Path", value="", placeholder="folder/subfolder/", key=f"folder_path_{storage_id}")
        
        with col2:
            if st.button("🔄 Refresh", key=f"file_refresh_{storage_id}", help="Refresh file list"):
                st.rerun()
        
        with col3:
            # Upload section toggle
            if st.button("📤 Upload Files", key=f"upload_toggle_{storage_id}"):
                st.session_state[f"show_upload_{storage_id}"] = not st.session_state.get(f"show_upload_{storage_id}", False)
        
        # Upload section
        if st.session_state.get(f"show_upload_{storage_id}", False):
            self.show_upload_interface(storage_id, prefix)
        
        # List and display files
        self.show_file_list(storage_id, prefix)
    
    def show_upload_interface(self, storage_id: str, prefix: str = ""):
        """Display file upload interface"""
        with st.expander("📤 Upload Files", expanded=True, key=f"upload_expander_{storage_id}"):
            st.write("Select files to upload to your storage bucket")
            
            # File uploader
            uploaded_files = st.file_uploader(
                "Choose files",
                accept_multiple_files=True,
                key=f"uploader_{storage_id}",
                help="You can upload multiple files at once"
            )
            
            # Upload path
            upload_path = st.text_input(
                "Upload to folder",
                value=prefix,
                placeholder="folder/subfolder/",
                key=f"upload_path_{storage_id}",
                help="Leave empty to upload to root folder"
            )
            
            if uploaded_files:
                st.write(f"Selected {len(uploaded_files)} file(s):")
                total_size = 0
                for file in uploaded_files:
                    st.write(f"• {file.name} ({self.format_size(file.size)})")
                    total_size += file.size
                
                st.info(f"Total size: {self.format_size(total_size)}")
                
                # Upload button
                if st.button("🚀 Upload Files", key=f"upload_btn_{storage_id}", type="primary"):
                    self.upload_files(storage_id, uploaded_files, upload_path)
    
    def upload_files(self, storage_id: str, files: List, upload_path: str = ""):
        """Upload files to storage"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        success_count = 0
        error_count = 0
        
        for i, file in enumerate(files):
            try:
                status_text.text(f"Uploading {file.name}...")
                
                # Get proper content type
                content_type = file.type if file.type else 'application/octet-stream'
                
                # Prepare the file data with proper content type
                files_data = {
                    'file': (file.name, file.getvalue(), content_type)
                }
                
                # Upload parameters
                params = {}
                if upload_path:
                    params['path'] = upload_path.strip('/')
                
                # Make upload request
                response = self.api_client.post(
                    f"/storage/{storage_id}/upload",
                    files=files_data,
                    params=params
                )
                
                if response.status_code == 200:
                    success_count += 1
                    logger.info("File uploaded successfully", 
                               storage_id=storage_id,
                               filename=file.name,
                               size=file.size)
                else:
                    error_count += 1
                    logger.error("Failed to upload file", 
                                storage_id=storage_id,
                                filename=file.name,
                                status_code=response.status_code)
                
            except Exception as e:
                error_count += 1
                logger.error("Error uploading file", 
                            storage_id=storage_id,
                            filename=file.name,
                            error=str(e))
            
            # Update progress
            progress_bar.progress((i + 1) / len(files))
        
        # Show results
        status_text.empty()
        progress_bar.empty()
        
        if success_count > 0:
            st.success(f"✅ Successfully uploaded {success_count} file(s)")
        
        if error_count > 0:
            st.error(f"❌ Failed to upload {error_count} file(s)")
        
        # Reset the uploader
        if success_count > 0:
            st.session_state[f"show_upload_{storage_id}"] = False
            st.rerun()
    
    def show_file_list(self, storage_id: str, prefix: str = ""):
        """Display list of files in storage"""
        try:
            # Get file list from API
            params = {}
            if prefix:
                params['prefix'] = prefix
            
            response = self.api_client.get(f"/storage/{storage_id}/list", params=params)
            
            if response.status_code != 200:
                st.error("Failed to load file list")
                return
            
            data = response.json()
            all_objects = data.get('objects', [])
            
            # Filter out hidden files/folders (starting with .)
            # Check both the full path and just the filename
            objects = []
            for obj in all_objects:
                obj_name = obj.get('name', '')
                # Skip if the filename starts with . or if any part of the path starts with .
                path_parts = obj_name.split('/')
                is_hidden = any(part.startswith('.') for part in path_parts if part)
                if not is_hidden:
                    objects.append(obj)
            
            if not objects:
                st.info("📭 No files found in this location")
                return
            
            # Display files in a nice format
            st.write(f"**{len(objects)} file(s) found**")
            
            # Create columns for the file list header
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            with col1:
                st.write("**📄 File Name**")
            with col2:
                st.write("**📏 Size**")
            with col3:
                st.write("**📅 Created**")
            with col4:
                st.write("**⬇️ Download**")
            with col5:
                st.write("**🗑️ Delete**")
            
            st.divider()
            
            # Display each file
            for obj in objects:
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                
                with col1:
                    # File icon based on type
                    file_icon = self.get_file_icon(obj['name'])
                    st.write(f"{file_icon} {os.path.basename(obj['name'])}")
                    if '/' in obj['name']:
                        st.caption(f"📁 {os.path.dirname(obj['name'])}")
                
                with col2:
                    st.write(self.format_size(obj.get('size', 0)))
                
                with col3:
                    created = obj.get('created')
                    if created:
                        try:
                            dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                            st.write(dt.strftime("%m/%d/%y"))
                        except:
                            st.write("Unknown")
                    else:
                        st.write("Unknown")
                
                with col4:
                    # Direct download approach
                    download_key = f"download_{storage_id}_{hash(obj['name'])}"
                    if st.button("⬇️", key=f"file_download_{storage_id}_{hash(obj['name'])}", help="Download file"):
                        st.session_state[download_key] = True
                        st.rerun()
                    
                    # Show download button if requested
                    if st.session_state.get(download_key, False):
                        try:
                            response = self.api_client.get(f"/storage/{storage_id}/download/{obj['name']}", stream=True)
                            if response.status_code == 200:
                                filename = os.path.basename(obj['name'])
                                st.download_button(
                                    label=f"💾 {filename}",
                                    data=response.content,
                                    file_name=filename,
                                    mime=response.headers.get('content-type', 'application/octet-stream'),
                                    key=f"dl_btn_{storage_id}_{hash(obj['name'])}",
                                    on_click=lambda: st.session_state.pop(download_key, None)
                                )
                            else:
                                st.error("Download failed")
                                st.session_state.pop(download_key, None)
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            st.session_state.pop(download_key, None)
                
                with col5:
                    delete_key = f"delete_{storage_id}_{hash(obj['name'])}"
                    if st.button("🗑️", key=f"file_delete_{storage_id}_{hash(obj['name'])}", help="Delete file"):
                        st.session_state[delete_key] = True
                        st.rerun()
                    
                    # Show delete confirmation if requested
                    if st.session_state.get(delete_key, False):
                        filename = os.path.basename(obj['name'])
                        st.warning(f"Delete {filename}?")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("❌", key=f"cancel_{storage_id}_{hash(obj['name'])}", help="Cancel"):
                                st.session_state.pop(delete_key, None)
                                st.rerun()
                        with col_b:
                            if st.button("✅", key=f"confirm_{storage_id}_{hash(obj['name'])}", help="Confirm delete"):
                                try:
                                    response = self.api_client.delete(f"/storage/{storage_id}/objects/{obj['name']}")
                                    if response.status_code == 200:
                                        st.success(f"Deleted {filename}")
                                        st.session_state.pop(delete_key, None)
                                        st.rerun()
                                    else:
                                        st.error("Delete failed")
                                        st.session_state.pop(delete_key, None)
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                                    st.session_state.pop(delete_key, None)
            
        except Exception as e:
            st.error(f"Error loading files: {str(e)}")
            logger.error("Error loading file list", 
                        storage_id=storage_id,
                        prefix=prefix,
                        error=str(e))
    
    def get_file_icon(self, filename: str) -> str:
        """Get appropriate icon for file type"""
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']:
            return "🖼️"
        elif ext in ['.pdf']:
            return "📄"
        elif ext in ['.doc', '.docx']:
            return "📝"
        elif ext in ['.xls', '.xlsx']:
            return "📊"
        elif ext in ['.ppt', '.pptx']:
            return "📈"
        elif ext in ['.txt', '.md']:
            return "📃"
        elif ext in ['.py', '.js', '.html', '.css', '.json']:
            return "💻"
        elif ext in ['.zip', '.rar', '.tar', '.gz']:
            return "📦"
        elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
            return "🎥"
        elif ext in ['.mp3', '.wav', '.flac']:
            return "🎵"
        else:
            return "📄"
    
    def download_file(self, storage_id: str, object_path: str):
        """Download a file from storage"""
        try:
            # Make download request
            response = self.api_client.get(
                f"/storage/{storage_id}/download/{object_path}",
                stream=True
            )
            
            if response.status_code == 200:
                # Get filename
                filename = os.path.basename(object_path)
                
                # Direct download without additional button
                st.download_button(
                    label=f"💾 Download {filename}",
                    data=response.content,
                    file_name=filename,
                    mime=response.headers.get('content-type', 'application/octet-stream'),
                    key=f"direct_download_{storage_id}_{hash(object_path)}",
                    use_container_width=True
                )
                
            else:
                st.error("Failed to download file")
                
        except Exception as e:
            st.error(f"Error downloading file: {str(e)}")
            logger.error("Error downloading file", 
                        storage_id=storage_id,
                        object_path=object_path,
                        error=str(e))
