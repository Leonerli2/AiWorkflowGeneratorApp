# UploadApp.py
import streamlit as st
import os
import subprocess
import argparse


# Function to handle video conversion
def convert_mov_to_mp4(mov_file, output_dir):
    output_path = os.path.join(output_dir, mov_file.name.split('.')[0] + '.mp4')
    command = f"ffmpeg -i {mov_file.name} -vcodec libx264 -acodec aac {output_path}"
    subprocess.run(command, shell=True)
    return output_path


def main(video_main_folder_path):

    st.title("Upload Video")

    # File uploader for video file
    video_file = st.file_uploader("Choose a Video", type=["mp4", "avi", "mov"])

    if video_file:
        st.write("Video uploaded successfully!")

        # Convert MOV to MP4
        if video_file.name.endswith(".mov"):
            st.write("Converting MOV to MP4...")
            video_file = convert_mov_to_mp4(video_file, video_main_folder_path)
            st.write("Conversion complete!")

        # Save the uploaded file
        # Find the next available video number
        video_files = os.listdir(video_main_folder_path)
        video_numbers = [int(file.split("video")[1].split(".")[0]) for file in video_files if file.startswith("video")]
        next_video_number = max(video_numbers) + 1 if video_numbers else 1
        video_file_path = os.path.join(video_main_folder_path, f"video{next_video_number}.mp4")
        with open(video_file_path, "wb") as f:
            f.write(video_file.read())
        st.write(f"Video saved to {video_file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Upload App")
    parser.add_argument("video_main_folder_path", type=str, help="Path to the main video folder")
    args = parser.parse_args()
    main(args.video_main_folder_path)