import streamlit as st
from pathlib import Path
import time
from object_storage import ObjectStorage
import load_environment

env = load_environment.load_env()
object_storage = ObjectStorage()

# Page configuration
st.set_page_config(page_title="Multi-Function App", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

# Main title
st.title("Multi-Function Dashboard")

# Create three columns
col1, col2, col3 = st.columns(3)

# Column 1: File Upload
with col1:
    st.header("📁 File Upload")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a file to upload",
        type=["txt", "pdf", "csv", "xlsx", "jpg", "png", "mp3", "wav", "docx"],
        help="Upload files to cloud storage"
    )
    
    # Handle file upload
    if uploaded_file is not None:
        # Create a unique identifier for this file (name + size + type)
        file_id = f"{uploaded_file.name}_{uploaded_file.size}_{uploaded_file.type}"
        
        # Only upload if this is a new file (not the same one from before rerun)
        if file_id != st.session_state.last_uploaded_file:
            # Show upload progress
            with st.spinner(f"Uploading {uploaded_file.name}..."):
                success, result = object_storage.document_upload(
                    uploaded_file,
                    "/files",
                    uploaded_file.name
                )
        
            if success:
                st.success(f"✓ {uploaded_file.name} uploaded successfully!")
                # Mark this file as uploaded
                st.session_state.last_uploaded_file = file_id
                st.rerun()  # Refresh to show in file list
            else:
                st.error(f"Upload failed: {result}")
        else:
            # File was already uploaded, just show success message
            st.info(f"✓ {uploaded_file.name} already uploaded")
    
    st.divider()
    
    # Display all uploaded files from cloud storage
    st.subheader("Your Files")
    
    files = object_storage.get_objects("/files")
    
    if files:
        # Create scrollable container for files
        file_container = st.container(height=400)
        
        with file_container:
            for idx, file_info in enumerate(files):
                # Create a card-like display for each file
                with st.container():
                    col_icon, col_info, col_actions = st.columns([1, 6, 2])
                    
                    with col_icon:
                        # File type icon
                        file_type = file_info.get("type", "")
                        if "image" in file_type:
                            st.write("🖼️")
                        elif "pdf" in file_type:
                            st.write("📄")
                        elif "audio" in file_type:
                            st.write("🎵")
                        elif "excel" in file_type or "sheet" in file_type:
                            st.write("📊")
                        elif "word" in file_type or "document" in file_type:
                            st.write("📝")
                        else:
                            st.write("📎")
                    
                    with col_info:
                        st.write(f"**{file_info['name']}**")
                        st.caption(f"{file_info['size'] / 1024:.1f} KB")
                    
                    with col_actions:
                        # Delete button
                        if st.button("🗑️", key=f"delete_{idx}"):
                            # Construct relative path: "files/filename.ext"
                            rel_path = f"files/{file_info['name']}"
                            success = object_storage.document_delete(rel_path)
                            if success:
                                st.success("File deleted!")
                            st.rerun()
                    
                    st.divider()
    else:
        st.info("No files uploaded yet. Upload a file to get started!")
    
    # Refresh button
    if st.button("🔄 Refresh File List", use_container_width=True):
        st.rerun()

# Column 2: Claude Chat
with col2:
    st.header("💬 Claude Chat")
    
    # API key input (or could be stored in backend)
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        help="Enter your Anthropic API key"
    )
    
    # Display chat messages
    chat_container = st.container(height=400)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask Claude anything..."):
        # Add user message to session state
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with chat_container:
            with st.chat_message("user"):
                st.write(prompt)
        
        # Get Claude response
        if api_key:
            # ========================================
            # BACKEND CALL MARKER #5
            # TODO: Call backend function to get Claude response
            # Example: 
            # response = backend.get_claude_response(
            #     api_key=api_key,
            #     messages=st.session_state.messages
            # )
            # ========================================
            
            # Placeholder for backend response
            # In production, replace this with actual backend call
            try:
                with chat_container:
                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        
                        # ========================================
                        # BACKEND CALL MARKER #6
                        # TODO: Handle streaming response from backend
                        # Example:
                        # full_response = ""
                        # for chunk in backend.stream_claude_response(
                        #     api_key=api_key,
                        #     messages=st.session_state.messages
                        # ):
                        #     full_response += chunk
                        #     message_placeholder.write(full_response + "▌")
                        # message_placeholder.write(full_response)
                        # ========================================
                        
                        # Temporary placeholder response
                        full_response = "Backend connection needed. Please implement backend.get_claude_response()"
                        message_placeholder.write(full_response)
                
                # Store assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response
                })
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter your Anthropic API key to chat with Claude.")
    
    st.divider()
    
    # Clear chat button
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        
        # ========================================
        # BACKEND CALL MARKER #7
        # TODO: Call backend to clear chat history if stored
        # Example: backend.clear_chat_history()
        # ========================================
        
        st.rerun()

# Column 3: MP3 Player
with col3:
    st.header("🎵 MP3 Player")
    
    # Upload MP3 file
    audio_file = st.file_uploader(
        "Upload an MP3 file",
        type=["mp3", "wav", "ogg"],
        key="audio_uploader"
    )
    
    if audio_file is not None:
        st.success(f"Loaded: {audio_file.name}")
        
        # ========================================
        # BACKEND CALL MARKER #8
        # TODO: Call backend to process/store audio file
        # Example: backend.store_audio_file(audio_file)
        # ========================================
        
        # Display audio player
        st.audio(audio_file, format=f"audio/{audio_file.type.split('/')[-1]}")
        
        # Audio file info
        st.write(f"File size: {audio_file.size / 1024:.2f} KB")
    else:
        st.info("Upload an audio file to play it here")
    
    st.divider()
    
    # Playlist section
    st.subheader("Playlist")
    
    # ========================================
    # BACKEND CALL MARKER #9
    # TODO: Call backend to retrieve playlist
    # Example: playlist = backend.get_playlist()
    # Display playlist items here
    # ========================================
    
    # Placeholder playlist container (same height as file list)
    playlist_container = st.container(height=400)
    with playlist_container:
        st.write("No playlist items yet")
    
    # Sample controls
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("⏮️ Previous"):
            # ========================================
            # BACKEND CALL MARKER #10
            # TODO: Call backend to get previous track
            # Example: backend.previous_track()
            # ========================================
            pass
    with col_b:
        if st.button("⏯️ Play/Pause"):
            # ========================================
            # BACKEND CALL MARKER #11
            # TODO: Call backend to toggle play/pause
            # Example: backend.toggle_playback()
            # ========================================
            pass
    with col_c:
        if st.button("⏭️ Next"):
            # ========================================
            # BACKEND CALL MARKER #12
            # TODO: Call backend to get next track
            # Example: backend.next_track()
            # ========================================
            pass

# Footer
st.markdown("---")
st.caption("Simple Streamlit Dashboard with File Upload, Claude Chat, and MP3 Player")