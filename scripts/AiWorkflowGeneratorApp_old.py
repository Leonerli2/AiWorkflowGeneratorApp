import streamlit as st

import os
import json
import subprocess
import atexit
from contextlib import contextmanager
import base64


from video2json import *
from json2json import *
from flowchart import *
from AiWizzard import *


VIDEO_PATH_HANDLER = VideoPathHandler(
    video_dir="data/input/videos",
    audio_dir="data/output/video/audio",
    transcription_with_timestamps_json_dir="data/output/video/transcription_with_timestamps",
    instructions_with_timestamps_json_dir="data/output/video/instructions_with_timestamps",
    instructions_basic_json_dir="data/output/video/instructions_basic",
    instructions_advanced_json_dir="data/output/video/instructions_advanced",
    elam_json_dir="data/output/video/elam",
    image_output_dir="data/output/video/images"
)

# Global variable to store the subprocess reference
elam_simulation_process = None

# Ensure port counter is initialized in session_state
if "elam_port_counter" not in st.session_state:
    st.session_state.elam_port_counter = 8502  # Starting port number for the first process

# Cleanup subprocess when the app is closed
@contextmanager
def manage_process():
    global elam_simulation_process
    try:
        yield
    finally:
        if elam_simulation_process:
            print("Terminating ELAM simulation subprocess...")
            elam_simulation_process.terminate()
            elam_simulation_process.wait()  # Ensure the process is fully terminated before starting a new one
            elam_simulation_process = None

# Register cleanup function using atexit
atexit.register(lambda: manage_process())


# Main Interface
def main():
    global elam_simulation_process

    st.sidebar.title("BOSSARD - AI Workflow Generator App")

    # Switch to choose between Video or PDF Mode
    mode = st.sidebar.radio("Choose Mode", ["Video", "PDF"])
    video_nr = None

    if "ai_wizard_started" not in st.session_state:
        st.session_state.ai_wizard_started = False
    if "ai_wizard_confirmed" not in st.session_state:
        st.session_state.ai_wizard_confirmed = False

    if mode == "Video":
        st.title("Video Management")
        
        # Video Mode Buttons
        video_file = st.file_uploader("Choose Video", type=["mp4", "avi", "mov"])

        if video_file:
            st.video(video_file)
            video_nr = video_file.name.split("video")[1].split('.')[0]

            # Create three columns for the buttons
            col1, col2, col3 = st.columns([1, 1, 1])  # 1 unit of space per column, adjust if needed
            with col1:
                ai_wizard_button = st.button("Start AI-Wizard")
            with col2:
                elam_sim_button = st.button("Start ELAM Sim")
            with col3:
                flowchart_button = st.button("Display Flowchart")

            # AI Wizard Confirmation
            if ai_wizard_button or st.session_state.ai_wizard_started:
                st.session_state.ai_wizard_started = True
                st.write("Are you sure you want to start the AI-Wizard?")
                confirm = st.button("Yes, start AI-Wizard")
                cancel = st.button("Cancel")

                if confirm:
                    st.session_state.ai_wizard_confirmed = True
                    st.session_state.ai_wizard_started = False
                    st.write("Starting AI-Wizard...")  # Show in Streamlit UI
                    print("Starting AI-Wizard...")  # Terminal feedback
                    AI_wizzard_video_2_elam_json(video_nr, VIDEO_PATH_HANDLER)
                    st.write("AI-Wizard completed.")
                elif cancel:
                    st.session_state.ai_wizard_started = False
                    st.write("AI-Wizard start canceled.")

            # ELAM Simulation
            if elam_sim_button:
                flowchart_path = VIDEO_PATH_HANDLER.get_elam_json_path(video_nr)
                if os.path.exists(flowchart_path):
                    # Increment port counter and launch subprocess with new port
                    st.session_state.elam_port_counter += 1
                    elam_simulation_process = subprocess.Popen(["streamlit", "run", "scripts/ELAMSimulationApp.py", "--server.port", str(st.session_state.elam_port_counter), "--", flowchart_path])
                    st.write(f"Started ELAM simulation on port {st.session_state.elam_port_counter}.")
                else:
                    st.write(f"No ELAM JSON found for this video under ({flowchart_path}).")

            # Flowchart Display
            if flowchart_button:
                flowchart_path = VIDEO_PATH_HANDLER.get_elam_json_path(video_nr)
                if os.path.exists(flowchart_path):
                    show_flowchart(flowchart_path)
                else:
                    st.write(f"No ELAM JSON found for this video under {flowchart_path}.")

    elif mode == "PDF":
        st.title("PDF Management")
        
        # PDF Mode Buttons
        pdf_file = st.file_uploader("Choose PDF", type=["pdf"])

        if pdf_file:
            st.write(f"PDF file {pdf_file.name} loaded.")



            pdf_nr = pdf_file.name.split("pdf")[1].split('.')[0]


            # Create three columns for the buttons
            col1, col2, col3 = st.columns([1, 1, 1])  # 1 unit of space per column, adjust if needed
            with col1:
                ai_wizard_button = st.button("Start AI-Wizard")
            with col2:
                elam_sim_button = st.button("Start ELAM Sim")
            with col3:
                flowchart_button = st.button("Display Flowchart")

            # AI Wizard Confirmation
            if ai_wizard_button or st.session_state.ai_wizard_started:
                st.session_state.ai_wizard_started = True
                st.write("Are you sure you want to start the AI-Wizard?")
                confirm = st.button("Yes, start AI-Wizard")
                cancel = st.button("Cancel")

                if confirm:
                    st.session_state.ai_wizard_confirmed = True
                    st.session_state.ai_wizard_started = False
                    st.write("Starting AI-Wizard...")  # Show in Streamlit UI
                    print("Starting AI-Wizard...")  # Terminal feedback
                    AI_wizzard_pdf_2_elam_json(pdf_nr, PDF_PATH_HANDLER)
                    st.write("AI-Wizard completed.")
                elif cancel:
                    st.session_state.ai_wizard_started = False
                    st.write("AI-Wizard start canceled.")

            # ELAM Simulation
            if elam_sim_button:
                flowchart_path = PDF_PATH_HANDLER.get_elam_json_path(pdf_nr)
                if os.path.exists(flowchart_path):
                    # Increment port counter and launch subprocess with new port
                    st.session_state.elam_port_counter += 1
                    elam_simulation_process = subprocess.Popen(["streamlit", "run", "scripts/ELAMSimulationApp.py", "--server.port", str(st.session_state.elam_port_counter), "--", flowchart_path])
                    st.write(f"Started ELAM simulation on port {st.session_state.elam_port_counter}.")
                else:
                    st.write(f"No ELAM JSON found for this video under ({flowchart_path}).")

            # Flowchart Display
            if flowchart_button:
                flowchart_path = PDF_PATH_HANDLER.get_elam_json_path(pdf_nr)
                if os.path.exists(flowchart_path):
                    show_flowchart(flowchart_path)
                else:
                    st.write(f"No ELAM JSON found for this video under {flowchart_path}.")


def show_pdf(file_path):
    with open(file_path, "rb") as pdf_file:
        base64_pdf = base64.b64encode(pdf_file.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="800" style="border: none;"></iframe>'
    st.components.v1.html(pdf_display, height=800)
    print("PDF displayed.")

# Function to show the flowchart
def show_flowchart(flowchart_path):
    try:
        # Load JSON data
        with open(flowchart_path) as f:
            flowchart_data = json.load(f)
        
        # Generate the flowchart using the imported function
        flowchart = create_flowchart_with_icons(flowchart_data, scale_factor=8.0, max_nodes_per_column=12)

        # Display the flowchart using Streamlit
        st.title("Interactive Flowchart")
        st.plotly_chart(flowchart, use_container_width=True)
    except Exception as e:
        st.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
