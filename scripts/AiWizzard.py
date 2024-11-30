from video2json import *
from json2json import *
from convert_pdf2simple_json import Convert_PDF_to_JSON


class PDFPathHandler:
    def __init__(self, pdf_dir: str, pdf_basic_json_dir: str, instructions_basic_json_dir: str, instructions_advanced_json_dir: str, elam_json_dir: str, image_output_dir: str):
        self.pdf_dir = pdf_dir
        self.pdf_basic_json_dir = pdf_basic_json_dir
        self.instructions_basic_json_dir = instructions_basic_json_dir
        self.instructions_advanced_json_dir = instructions_advanced_json_dir
        self.elam_json_dir = elam_json_dir
        self.image_output_dir = image_output_dir

    def get_pdf_path(self, pdf_nr):
        return f"{self.pdf_dir}/w{pdf_nr}.pdf"
    
    def get_pdf_basic_json_path(self, pdf_nr):
        return f"{self.pdf_basic_json_dir}/w{pdf_nr}.json"
    
    def get_instructions_basic_json_path(self, pdf_nr):
        return f"{self.instructions_basic_json_dir}/instructions_basic{pdf_nr}.json"
    
    def get_instructions_advanced_json_path(self, pdf_nr):
        return f"{self.instructions_advanced_json_dir}/instructions_advanced{pdf_nr}.json"
    
    def get_elam_json_path(self, pdf_nr):
        return f"{self.elam_json_dir}/elam{pdf_nr}.json"
    
    def get_image_output_dir(self, pdf_nr):
        return f"{self.image_output_dir}/w{pdf_nr}"

  
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


def AI_wizzard_pdf_2_elam_json(pdf_nr, pdf_path_handler):
    print(f"### Starting AI-Wizard for PDF {pdf_nr}.")

    # Convert the PDF to basic JSON
    pdf_path = pdf_path_handler.get_pdf_path(pdf_nr)
    Convert_PDF_to_JSON(pdf_path)

    # Convert the PDF basic JSON to basic instruction JSON
    pdf_basic_json_path = pdf_path_handler.get_pdf_basic_json_path(pdf_nr)
    output_json_path = pdf_path_handler.get_instructions_basic_json_path(pdf_nr)
    pdf_basic_json_2_instruction_basic_json(pdf_basic_json_path, output_json_path)

    # Convert the basic instruction JSON to an advanced instruction JSON
    instructions_basic_json_path = pdf_path_handler.get_instructions_basic_json_path(pdf_nr)
    output_json_path = pdf_path_handler.get_instructions_advanced_json_path(pdf_nr)
    instruction_basic_json_2_instruction_advanced_json(instructions_basic_json_path, output_json_path)

    # Convert the advanced instruction JSON to ELAM JSON
    instructions_advanced_json_path = pdf_path_handler.get_instructions_advanced_json_path(pdf_nr)
    output_json_path = pdf_path_handler.get_elam_json_path(pdf_nr)
    instruction_advanced_json_2_elam_flowchart_json(instructions_advanced_json_path, output_json_path)