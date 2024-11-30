from video2json import *
from json2json import *
from convert_pdf2simple_json import Convert_PDF_to_JSON

OPENAI_API_KEY = "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"


pdf_nr = 5


class PDFPathHandler:
    def __init__(self, pdf_dir: str, pdf_basic_json_dir: str, instructions_basic_json_dir: str, instructions_advanced_json_dir: str, elam_json_dir: str, image_output_dir: str):
        self.pdf_dir = pdf_dir
        self.pdf_basic_json_dir = pdf_basic_json_dir
        self.instructions_basic_json_dir = instructions_basic_json_dir
        self.instructions_advanced_json_dir = instructions_advanced_json_dir
        self.elam_json_dir = elam_json_dir
        self.image_output_dir = image_output_dir

    def get_pdf_path(self, pdf_nr):
        return f"{self.pdf_dir}/w{pdf_nr}.mp4"
    
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
    


pdf_path_handler = PDFPathHandler(
    pdf_dir="data/input/pdfs",
    pdf_basic_json_dir="cache/jsons",
    instructions_basic_json_dir="data/output/pdf/instructions_basic",
    instructions_advanced_json_dir="data/output/pdf/instructions_advanced",
    elam_json_dir="data/output/pdf/elam",
    image_output_dir="data/output/pdf/images"
)

if True:
    # Convert the PDF to basic JSON
    pdf_path = pdf_path_handler.get_pdf_path(pdf_nr)

    Convert_PDF_to_JSON(pdf_path)


if True:
    # Convert the PDF basic JSON to basic instruction JSON
    pdf_basic_json_path = pdf_path_handler.get_pdf_basic_json_path(pdf_nr)
    output_json_path = pdf_path_handler.get_instructions_basic_json_path(pdf_nr)

    pdf_basic_json_2_instruction_basic_json(pdf_basic_json_path, output_json_path)

if True:
    # Convert the basic instruction JSON to an advanced instruction JSON
    instructions_basic_json_path = pdf_path_handler.get_instructions_basic_json_path(pdf_nr)
    output_json_path = pdf_path_handler.get_instructions_advanced_json_path(pdf_nr)

    instruction_basic_json_2_instruction_advanced_json(instructions_basic_json_path, output_json_path)

if True:
    # Convert the advanced instruction JSON to ELAM JSON
    instructions_advanced_json_path = pdf_path_handler.get_instructions_advanced_json_path(pdf_nr)
    output_json_path = pdf_path_handler.get_elam_json_path(pdf_nr)

    instruction_advanced_json_2_elam_flowchart_json(instructions_advanced_json_path, output_json_path)