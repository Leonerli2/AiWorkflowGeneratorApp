import tkinter as tk
from tkinter import filedialog, Label, Button
import cv2
from PIL import Image, ImageTk
import os
import re
import json
from ffpyplayer.player import MediaPlayer
from utils import extract_audio, audio_text_extraction_timestamps, extract_instructions_from_text, extract_frames

# Initialize the main application window and hide it
root = tk.Tk()
root.withdraw()

# Create two separate windows
left_window = tk.Toplevel(root)
left_window.title("Workflow Generator - Video")
left_window.geometry("400x500")

right_window = tk.Toplevel(root)
right_window.title("Workflow Generator - Instructions")
right_window.geometry("400x500")

# Variables to hold video capture and loop status
video_path = None
video_number = None
cap = None
player = None
playing = False
instructions = []

# Variable to keep track of the current instruction index
current_instruction = tk.IntVar()

# Function to choose a video file
def choose_video():
    global video_path, video_number, directory_path, cap, playing, instructions, player
    video_path = filedialog.askopenfilename(title="Choose Video", filetypes=[("Video Files", "*.mp4")])
    if video_path:
        # Extract video number
        directory_path, video_number = extract_path_and_video_number(video_path)
        print(f"Video {video_number} selected.")
        # Load instructions from the corresponding JSON file
        try:
            instructions_path = os.path.join(directory_path, f"src/instructions{video_number}.json")
            with open(instructions_path, 'r') as file:
                instructions = json.load(file)["steps"]
            current_instruction.set(0)  # Start at the first instruction
            update_instruction()
            
            # Release previous video capture if any
            if cap:
                cap.release()
            # Initialize video capture with the new file
            cap = cv2.VideoCapture(video_path)
            
            # Initialize audio player
            player = MediaPlayer(video_path)

            # Set label size to match video dimensions
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            video_label.config(width=320, height=200)
            
            playing = True
            play_video()
        except FileNotFoundError:
            print(f"Instructions file not found for video {video_number}. Convert the video.")

def start_video():
    global video_path, video_number, directory_path, cap, playing, instructions, player
    if video_path:
        # Extract video number
        directory_path, video_number = extract_path_and_video_number(video_path)
        # Load instructions from the corresponding JSON file
        instructions_path = os.path.join(directory_path, f"src/instructions{video_number}.json")
        with open(instructions_path, 'r') as file:
            instructions = json.load(file)["steps"]
        current_instruction.set(0)  # Start at the first instruction
        update_instruction()
        
        # Release previous video capture if any
        if cap:
            cap.release()
        # Initialize video capture with the new file
        cap = cv2.VideoCapture(video_path)
        
        # Initialize audio player
        player = MediaPlayer(video_path)

        # Set label size to match video dimensions
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        video_label.config(width=320, height=200)
        
        playing = True
        play_video()

# Function to convert the video to instructions
def convert_video():
    global video_path, video_number, directory_path, cap, playing, instructions, player
    print(f"Converting video {video_number}...")
    video_nr = video_number
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    video_path = f"Videos/video{video_nr}.mp4"
    audio_path = f"src/audio{video_nr}.mp3"
    json_input_path = f"src/transcript{video_nr}.json"
    json_output_path = f"src/instructions{video_nr}.json"
    pictures_path = f"src/pictures"

    extract_audio(video_path, audio_path)
    print("Audio extracted")
    audio_text_extraction_timestamps(audio_path, json_input_path)
    print("Audio extracted and transcribed")
    extract_instructions_from_text(json_input_path, json_output_path)
    print("Instructions extracted from text")
    extract_frames(video_nr, video_path, json_output_path, pictures_path)
    print("DONE")
    
    # wait 1s for the images to be saved correctly
    left_window.after(1000, lambda: start_video())
    
# Function to play the video with audio in a loop
def play_video():
    global cap, playing, player
    if playing and cap and player:
        ret, frame = cap.read()
        if ret:
            # Synchronize audio
            audio_frame, val = player.get_frame()
            if val != 'eof' and audio_frame is not None:
                # Process audio frame, playing it in sync with video
                player.get_pts()  # Update time to match video
                
            # Convert the frame to RGB and then to a format compatible with Tkinter
            frame = cv2.resize(frame, (320, 200))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.imgtk = imgtk
            video_label.configure(image=imgtk)
            # Loop after a delay (e.g., 20 ms)
            video_label.after(24, play_video)
        else:
            # Restart the video and audio when it reaches the end
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            player.seek(0)  # Reset audio to the start
            play_video()

# Function to stop video playback when window is closed
def on_closing():
    global cap, playing, player
    playing = False
    if cap:
        cap.release()
    if player:
        player.close()
    root.quit()

# Function to extract directory path and video number
def extract_path_and_video_number(path):
    directory_path = os.path.dirname(path)
    directory_path = os.path.dirname(directory_path)
    match = re.search(r'video(\d+)', os.path.basename(path), re.IGNORECASE)
    if match:
        video_number = match.group(1)
    else:
        video_number = None  # If no video number is found
    return directory_path, video_number

# Navigation and instruction update functions
def prev_instruction():
    current_idx = current_instruction.get()
    if current_idx > 0:
        current_instruction.set(current_idx - 1)
        update_instruction()

def next_instruction():
    current_idx = current_instruction.get()
    if current_idx < len(instructions) - 1:
        current_instruction.set(current_idx + 1)
        update_instruction()

def update_instruction():
    idx = current_instruction.get()
    description = instructions[idx]["description"]
    instruction_label.config(text=f"Instruction {idx + 1}: {description}")
    
    # path of gui.py file
    directory_path = os.path.dirname(os.path.abspath(__file__))
    
    # Resize image for display
    img = Image.open(f"{directory_path}/src/pictures/instruction{video_number}_{idx + 1}.jpg")
    img = img.resize((1280, 800), Image.LANCZOS)  # Use LANCZOS for better scaling
    imgtk = ImageTk.PhotoImage(img)
    img_label.config(image=imgtk)
    img_label.config(width=1000, height=600)
    img_label.image = imgtk  # Keep a reference to prevent garbage collection

    # Enable/disable navigation buttons based on the current instruction
    prev_button.config(state="normal" if idx > 0 else "disabled")
    next_button.config(state="normal" if idx < len(instructions) - 1 else "disabled")

def convert2pdf():
    # Styles for the PDF
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak 
    from reportlab.platypus import Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet

    styles = getSampleStyleSheet()
    story = []
    
    # Add instructions and images to the PDF story
    for i in range(len(instructions)):
        try:  # Ensure we don't go out of bounds
            img_path = os.path.join("src/pictures", f"instruction{video_number}_{i + 1}.jpg")
            if (i+1)%2 == 1 and i != 0:
                story.append(PageBreak())
            disc = instructions[i]["description"]
            story.append(Paragraph(f"Step {i + 1}: {disc}", styles["Normal"]))
            story.append(Spacer(1, 12))
            story.append(RLImage(img_path, width=300, height=200))  # Adjust image size as needed
            story.append(Spacer(1, 48))
        except FileNotFoundError:
            print(f"Image file not found for instruction {i + 1}")
    
    # Create the PDF
    doc = SimpleDocTemplate("output_pdf.pdf", pagesize=letter)
    doc.build(story)
    print("PDF created successfully")
   
# Load and add the image to the left window
def add_picture_to_left_frame(image_path):
    try:
        img = Image.open(image_path)
        img = img.resize((200, 200), Image.LANCZOS)  # Resize the image
        img_tk = ImageTk.PhotoImage(img)
        
        # Create a label to hold the image
        picture_label = Label(left_frame, image=img_tk, bg="lightgray")
        picture_label.image = img_tk  # Keep a reference to avoid garbage collection
        picture_label.pack(pady=10)
    except FileNotFoundError:
        print(f"Image not found: {image_path}")

# GUI Setup for Left Window
left_frame = tk.Frame(left_window, width=400, height=500, padx=10, pady=10, bg="lightgray")
left_frame.pack(fill="both", expand=True)

title_label = Label(left_frame, text="Workflow Generator", font=("Arial", 14), bg="lightgray")
title_label.pack(pady=10)

video_label = Label(left_frame, text="Video", font=("Arial", 12), width=40, height=6, bg="black", fg="white")
video_label.pack(pady=10)

choose_button = Button(left_frame, text="Choose Video", command=choose_video)
choose_button.pack(pady=5)

convert_button = Button(left_frame, text="Convert", command=convert_video)
convert_button.pack(pady=5)

contert_to_pdf_button = Button(left_frame, text="Convert to PDF", command=convert2pdf)
contert_to_pdf_button.pack(pady=5)

# Call the function with the path to your image
add_picture_to_left_frame("upload_url_qr.png")   

# GUI Setup for Right Window
right_frame = tk.Frame(right_window, width=400, height=500, padx=10, pady=10, bg="white")
right_frame.pack(fill="both", expand=True)

img_label = Label(right_frame, text="Img", font=("Arial", 12), relief="sunken", width=60, height=20)
img_label.pack(pady=5)

instruction_label = Label(right_frame, font=("Arial", 20), relief="sunken", width=50, height=6, anchor="w", justify="left", wraplength=800)
instruction_label.pack(pady=5)

nav_frame = tk.Frame(right_frame, bg="white")
nav_frame.pack(pady=5)

prev_button = Button(nav_frame, text="Prev", command=prev_instruction, font=("Arial", 20, "bold"), width=10, height=2)
prev_button.pack(side="left", padx=10, pady=10)

next_button = Button(nav_frame, text="Next", command=next_instruction, font=("Arial", 20, "bold"), width=10, height=2)
next_button.pack(side="left", padx=10, pady=10)

# Protocol handlers for window closing
left_window.protocol("WM_DELETE_WINDOW", on_closing)
right_window.protocol("WM_DELETE_WINDOW", on_closing)

# Start the GUI event loop
root.mainloop()
