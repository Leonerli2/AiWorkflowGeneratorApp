from utils import *
import os

# Change working directory to the directory containing this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

video_nr = 5

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