import streamlit as st
from pathlib import Path
import time
from object_storage import ObjectStorage
from chat import Chat
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

if "chat_instance" not in st.session_state:
    st.session_state.chat_instance = None

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

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
                    "files",
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
    
    files = object_storage.get_objects("files")
    
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
    
    # API key input
    api_key_input = st.text_input(
        "Anthropic API Key",
        value=st.session_state.api_key,
        type="password",
        help="Enter your Anthropic API key"
    )
    
    # Initialize chat instance when API key is provided
    if api_key_input and api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        st.session_state.chat_instance = Chat(api_key=api_key_input, tools=True)
        st.success("✓ Chat initialized!")
    
    # Display chat messages
    chat_container = st.container(height=400)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask Claude anything..."):
        if not st.session_state.chat_instance:
            st.warning("Please enter your Anthropic API key first.")
        else:
            # Add user message to session state
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with chat_container:
                with st.chat_message("user"):
                    st.write(prompt)
            
            # Get Claude response with streaming
            try:
                with chat_container:
                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        full_response = ""
                        
                        # Stream response from chat.py
                        for text_chunk in st.session_state.chat_instance.chat_stream(prompt):
                            full_response += text_chunk
                            message_placeholder.write(full_response + "▌")
                        
                        # Remove cursor
                        message_placeholder.write(full_response)
                
                # Store assistant response in UI messages
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response
                })
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.divider()
    
    # Clear chat button
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        if st.session_state.chat_instance:
            st.session_state.chat_instance.clear_chat()
        st.rerun()

# Column 3: MP3 Player
with col3:
    st.header("🎵 MP3 Player")
    
    # Get audio files from S3
    audio_files = object_storage.get_objects("podcasts")
    
    if audio_files:
        # Create a selectbox to choose audio file
        selected_audio = st.selectbox(
            "Choose a podcast to play",
            options=audio_files,
            format_func=lambda x: x['name']
        )
        
        if selected_audio:
            st.success(f"Now playing: {selected_audio['name']}")
            
            # Display audio player using the S3 URL
            st.audio(selected_audio['url'])
            
            # Audio file info
            st.write(f"File size: {selected_audio['size'] / 1024:.2f} KB")
            st.write(f"Uploaded: {selected_audio['uploaded_at']}")
    else:
        st.info("No podcasts available. Generate one using the chat!")
    
    st.divider()
    
    # Manual upload section
    st.subheader("Upload Audio")
    audio_file = st.file_uploader(
        "Upload an MP3 file",
        type=["mp3", "wav", "ogg"],
        key="audio_uploader"
    )
    
    if audio_file is not None:
        # Display audio player for uploaded file
        st.audio(audio_file, format=f"audio/{audio_file.type.split('/')[-1]}")
        st.write(f"File size: {audio_file.size / 1024:.2f} KB")
        
        # Option to save to S3
        if st.button("Save to Podcasts", use_container_width=True):
            with st.spinner("Uploading..."):
                success, result = object_storage.document_upload(
                    audio_file,
                    "podcasts",
                    audio_file.name
                )
                if success:
                    st.success("✓ Audio saved to podcasts!")
                    st.rerun()
                else:
                    st.error(f"Upload failed: {result}")
    
    # Refresh button
    if st.button("🔄 Refresh Podcasts", use_container_width=True):
        st.rerun()

# Footer
st.markdown("---")
st.caption("AI Podcast Generator - Upload files, chat with Claude, and listen to generated podcasts")