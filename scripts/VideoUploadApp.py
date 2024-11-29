# UploadApp.py
import streamlit as st

st.title("Upload Video")

# File uploader for video file
video_file = st.file_uploader("Choose a Video", type=["mp4", "avi", "mov"])

if video_file:
    st.write("Video uploaded successfully!")
    # Save the uploaded file (optional)
    with open(f"data/uploaded_videos/{video_file.name}", "wb") as f:
        f.write(video_file.getbuffer())
    st.success(f"Video '{video_file.name}' uploaded successfully.")
