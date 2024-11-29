from video2json import *
from json2json import *

def AI_wizzard_video_2_elam_json(video_nr, video_path_handler):
    print(f"### Starting AI-Wizard for video {video_nr}.")

    # Extract audio from the video
    video_path = video_path_handler.get_video_path(video_nr)
    audio_output = video_path_handler.get_audio_path(video_nr)

    extract_audio(video_path, audio_output)


    # Extract transcription with timestamps from the audio
    audio_file_path = video_path_handler.get_audio_path(video_nr)
    json_file_path = video_path_handler.get_transcription_with_timestamps_json_path(video_nr)
    
    audio_text_extraction_timestamps(audio_file_path, json_file_path)


    # Extract instructions from the video transcription with timestamps
    transcription_with_timestamps_json_path = video_path_handler.get_transcription_with_timestamps_json_path(video_nr)
    output_json_path = video_path_handler.get_instructions_with_timestamps_json_path(video_nr)

    instructions = video_transcription_with_timestamps_json_2_instructions_with_timestamps_json(transcription_with_timestamps_json_path, output_json_path)


    # Extract frames from the video
    video_path = video_path_handler.get_video_path(video_nr)
    instructions_json_path = video_path_handler.get_instructions_with_timestamps_json_path(video_nr)
    output_dir = video_path_handler.get_image_output_dir(video_nr)

    extract_frames(video_nr, video_path, instructions_json_path, output_dir)


    # Convert the instructions JSON to a basic instruction JSON
    instructions_with_timestamps_json_path = video_path_handler.get_instructions_with_timestamps_json_path(video_nr)
    output_json_path = video_path_handler.get_instructions_basic_json_path(video_nr)
    images_dir = video_path_handler.get_image_output_dir(video_nr)

    instructions_with_timestamps_json_2_basic_instruction_json(video_nr, instructions_with_timestamps_json_path, output_json_path, images_dir)


    # Convert the basic instruction JSON to an advanced instruction JSON
    instructions_basic_json_path = video_path_handler.get_instructions_basic_json_path(video_nr)
    output_json_path = video_path_handler.get_instructions_advanced_json_path(video_nr)

    instruction_basic_json_2_instruction_advanced_json(instructions_basic_json_path, output_json_path)


    # Bring into ELAM format
    instructions_advanced_json_path = video_path_handler.get_instructions_advanced_json_path(video_nr)
    output_json_path = video_path_handler.get_elam_json_path(video_nr)

    instruction_advanced_json_2_elam_flowchart_json(instructions_advanced_json_path, output_json_path)
