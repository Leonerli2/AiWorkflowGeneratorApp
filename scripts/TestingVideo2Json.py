from video2json import *
from json2json import *

OPENAI_API_KEY = "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"


video_nr = 51

path_handler = PathHandler(
    video_dir="data/input/videos",
    audio_dir="data/output/audio",
    transcription_with_timestamps_json_dir="data/output/transcription_with_timestamps",
    instructions_with_timestamps_json_dir="data/output/instructions_with_timestamps",
    instructions_basic_json_dir="data/output/instructions_basic",
    instructions_advanced_json_dir="data/output/instructions_advanced",
    elam_json_dir="data/output/elam",
    image_output_dir="data/output/images"
)

if True:
    # Extract audio from the video
    video_path = path_handler.get_video_path(video_nr)
    audio_output = path_handler.get_audio_path(video_nr)

    extract_audio(video_path, audio_output)

if True:
    # Extract transcription with timestamps from the audio
    audio_file_path = path_handler.get_audio_path(video_nr)
    json_file_path = path_handler.get_transcription_with_timestamps_json_path(video_nr)
    
    audio_text_extraction_timestamps(audio_file_path, json_file_path)

if True:
    # Extract instructions from the video transcription with timestamps
    transcription_with_timestamps_json_path = path_handler.get_transcription_with_timestamps_json_path(video_nr)
    output_json_path = path_handler.get_instructions_with_timestamps_json_path(video_nr)

    instructions = video_transcription_with_timestamps_json_2_instructions_with_timestamps_json(transcription_with_timestamps_json_path, output_json_path)

if True:
    # Extract frames from the video
    video_path = path_handler.get_video_path(video_nr)
    instructions_json_path = path_handler.get_instructions_with_timestamps_json_path(video_nr)
    output_dir = path_handler.get_image_output_dir(video_nr)

    extract_frames(video_nr, video_path, instructions_json_path, output_dir)

if True:
    # Convert the instructions JSON to a basic instruction JSON
    instructions_with_timestamps_json_path = path_handler.get_instructions_with_timestamps_json_path(video_nr)
    output_json_path = path_handler.get_instructions_basic_json_path(video_nr)
    images_dir = path_handler.get_image_output_dir(video_nr)

    instructions_with_timestamps_json_2_basic_instruction_json(video_nr, instructions_with_timestamps_json_path, output_json_path, images_dir)

if True:
    # Convert the basic instruction JSON to an advanced instruction JSON
    instructions_basic_json_path = path_handler.get_instructions_basic_json_path(video_nr)
    output_json_path = path_handler.get_instructions_advanced_json_path(video_nr)

    instruction_basic_json_2_instruction_advanced_json(instructions_basic_json_path, output_json_path)