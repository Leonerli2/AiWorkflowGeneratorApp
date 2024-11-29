##
from pydantic import BaseModel
from openai import OpenAI
import fitz
from pathlib import Path
import os
from PIL import Image
from openai import OpenAI
from io import BytesIO
import base64
import pickle
from dotenv import load_dotenv
import json
import tqdm
import time
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption   
import logging
import hashlib
import numpy as np
from skimage.metrics import structural_similarity as ssim
import math
import shutil
from picture_extraction_simple import extract_pictures

# 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

# Load the OpenAI API key from the environment variables
print(os.getenv("OPENAI_API_KEY"))
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

# -------------------------------------------------------------------------------------
#                      OpenAI Code for instruction extraction
# -------------------------------------------------------------------------------------
def structured_openai_api_call(img, system_prompt):
    """
      Args:
        img (PIL.Image.Image): The image to be processed.
         system_prompt (str): The system prompt to guide the model's response.
      Returns:
           List[InstructionStep]: A list of parsed instructions extracted from the image, each containing:
                - step (int): The step number.
                 - text (str): The instruction text.
                  - picture (bool): Whether a picture is associated with the step.
                   - picture_description (str): Description of the picture if applicable.
            - picture (bool): Whether a picture is associated with the step.
            - picture_description (str): Description of the picture if applicable.
    """
    img_uri = get_img_uri(img)
    
    client = OpenAI()

    # Define the JSON structure for the instructions
    class InstructionStep(BaseModel):
            step: int
            text: str
            picture: bool
            picture_description: str
    class Instruction(BaseModel):
        instructions: list[InstructionStep]
        
    

    # Structured API call to extract instructions
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": img_uri,
                        },
                    },
                ],
            }
        ],
        response_format=Instruction,  # Parse into the defined schema
    )

    # Extract the parsed instructions
    instructions = [choice.message.parsed for choice in completion.choices]

    # Output the results as JSON
    return instructions

def convert_pdfs_to_images(folder_path, dpi=60):
        """
        Convert all PDF files in a folder to images.

        Args:
            folder_path (str): Path to the folder containing PDF files
            dpi (int, optional): DPI for the output images. Defaults to 60

        Returns:
            list: List of images extracted from all PDFs
        """
        pdf_images = []
        folder_path = Path(folder_path)

        # Get all PDF files in the folder and sort them
        pdf_files = sorted(folder_path.glob('*.pdf'))

        if not pdf_files:
            print(f"No PDF files found in {folder_path}")
            return pdf_images

        # Process each PDF file
        for pdf_path in pdf_files:
            try:
                pdf_document = fitz.open(pdf_path)
                page_count = pdf_document.page_count

                for page_number in range(page_count):
                    try:
                        page = pdf_document[page_number]
                        matrix = fitz.Matrix(dpi/72, dpi/72)
                        pix = page.get_pixmap(matrix=matrix)
                        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        pdf_images.append(image)
                        
                    except Exception as e:
                        print(f"Error processing page {page_number + 1} of {pdf_path.name}: {str(e)}")
                        continue

                pdf_document.close()

                print(f"Successfully extracted images from {pdf_path.name}: {page_count} pages")

            except Exception as e:
                print(f"Error processing PDF {pdf_path.name}: {str(e)}")
                continue

        return pdf_images

def get_img_uri(img):
    """
    Converts a PIL Image object to a base64-encoded data URI.
    Args:
        img (PIL.Image.Image): The image to be converted.
    Returns:
        str: The base64-encoded data URI of the image.
    """
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{base64_image}"
    return data_uri
    
def analyze_image(img, system_prompt):
    """
    Analyzes an image using the OpenAI API and returns the response content.
    Args:
        img: The image to be analyzed.
        system_prompt (str): The system prompt to guide the analysis.
    Returns:
        str: The content of the response message from the OpenAI API. (non structured output)
    Raises:
        openai.error.OpenAIError: If there is an error with the OpenAI API request.
    """
    img_uri = get_img_uri(img)
    
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": img_uri,
                        },
                    },
                ],
            }
        ],
        max_tokens=3000,
        top_p=0.1
    )
    return response.choices[0].message.content

def normal_openai_api_call(system_prompt):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            }
        ],
        max_tokens=3000,
        top_p=0.1
    )
    return response.choices[0].message.content

def extract_text_from_pdf():
    """
      Ensure you have the following folder structure:
    - data/
        - input_pdf/ (place your PDF files here)
        - output_openai_text/ (the extracted instructions will be saved here as JSON)
    """

    # get current working directory
    cwd = Path.cwd() # not sure if this is the correct way to get the current working directory
    
    input_path_folder = cwd / "data/input_pdf"
    output_path_folder = cwd / "data/output_openai_text"
    
    pdf_files = list(input_path_folder.glob("*.pdf"))
    
    images = convert_pdfs_to_images(input_path_folder)
    
    # Initialize a dictionary to store instructions by page
    instructions_by_page = {}

    # Loop over the images and process them
    for i, image in enumerate(images):
        # Get the structured JSON for the current page
        instructions_list = structured_openai_api_call(
            image,
            "Extract all work instructions form the image. Order them in steps. Say if there is a corresponding picture (true/false) and add a picture description if applicable."
        )
                
        # Print progress
        print(f"Processed page {i+1}")
        # [Instruction(instructions=[InstructionStep(step=1, text='Zweck: Dient als Montagehilfe.', picture=False, picture_description=''), InstructionStep(step=2, text='Geltungsbereich: Dieses Dokument darf nur für internen Gebrauch verwendet werden.', picture=False, picture_description=''), InstructionStep(step=3, text='Definitionen (Begriffsklärung): Q-in-Line Qualitätsicherung in der Linie.', picture=False, picture_description=''), InstructionStep(step=4, text='Verfahren: Beschreibt die Vorgehensweise für eine Montagearbeit.', picture=False, picture_description=''), InstructionStep(step=5, text='Verantwortlichkeiten: Der Mitarbeiter ist im Sinne von Q in Line verantwortlich, dass die Montagetätigkeiten entsprechend den Verfahrensregelungen E-P003 PRODUKTE HERSTELLEN ausgeführt werden.', picture=False, picture_description='')])]

        # convert response to json
        page_key = f"page{i+1}"
        
        # Convert Instruction objects to dictionaries
        instructions_dicts = [instr.dict() for instr in instructions_list]
        instructions_by_page[page_key] = instructions_dicts
        
        
    print("Instructions extracted successfully.")
    # Output the result as a JSON string
    output_json = json.dumps(instructions_by_page, ensure_ascii=False, indent=4)

    
    # Optionally, save to a file
    with open(output_path_folder / "instructions_by_page.json", "w", encoding="utf-8") as file:
        file.write(output_json)
    
    return output_json

def custom_serializer(obj):
    if hasattr(obj, 'export_to_dict'):
        data = obj.export_to_dict()
        obj_id = id(obj)
        if obj_id in image_paths:
            data['image_path'] = image_paths[obj_id]
        return data
    else:
        return obj.__dict__



# -------------------------------------------------------------------------------------
#                                Docling Code
# -------------------------------------------------------------------------------------
def extract_text_and_pictures(input_doc_name: str = "data/input_pdf/w5.pdf"):
    output_dir = Path("data/output_docling")
    
    logging.basicConfig(level=logging.INFO)
    input_doc_path = Path(input_doc_name)

    # Set up pipeline options for OCR and table structure
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.images_scale = 4.0
    pipeline_options.do_table_structure = True
    pipeline_options.generate_picture_images = True  # Enable picture extraction

    # Initialize DocumentConverter with options
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    start_time = time.time()
    conv_result = doc_converter.convert(input_doc_path)
    end_time = time.time() - start_time

    logging.info(f"Document converted in {end_time:.2f} seconds.")

    # Export the entire document as JSON directly
    output_dir.mkdir(parents=True, exist_ok=True)
    json_output_path = output_dir / f"{input_doc_path.stem}.json"

    # Save images of figures and tables
    picture_output_dir = output_dir / "pictures"
    picture_output_dir.mkdir(parents=True, exist_ok=True)
    picture_counter = 0
    global image_paths
    image_paths = {}

    for element, _ in conv_result.document.iterate_items():
        if hasattr(element, "image") and element.image:
            picture_counter += 1
            picture_filename = f"picture_{picture_counter:03d}.jpg"
            picture_path = picture_output_dir / picture_filename
            with picture_path.open("wb") as fp:
                element.image.pil_image.save(fp, format="JPEG")
            # Use the object's id() as a unique identifier
            image_paths[id(element)] = str(Path("data/output_docling/pictures") / picture_filename)
            logging.info(f"Picture saved to {picture_path}")
             
            # add picture filename to the element (make new json entry) modify the json structure
            element.image.uri = str(Path("data\output_docling\pictures") / picture_filename)
    print("Creating JSON file...")        
         
    with json_output_path.open("w", encoding="utf-8") as fp:
        json.dump(conv_result.document, fp, default=custom_serializer, indent=2)

    logging.info(f"Full document JSON saved to {json_output_path}") 
    
    return conv_result.document   
       
def structured_openai_api_call_with_picture_json(json_input: dict, system_prompt: str):
    """
    Args:
        json_input (dict): A JSON object containing the instructions to be processed.
        system_prompt (str): The system prompt to guide the model's response.

    Returns:
        List[InstructionStep]: A list of parsed instructions extracted from the JSON input, each containing:
            - step (int): The step number.
            - text (str): The instruction text.
            - picture (bool): Whether a picture is associated with the step.
            - picture_description (str): Description of the picture if applicable.
    """
    output_dir = Path("data/output_docling")

    # Define the JSON structure for the instructions
    class Picture(BaseModel):
        page_no: int
        picture_uri: str
        center_x: int
        center_y: int

    class Pictures(BaseModel):
        pictures: list[Picture]

    # Instantiate OpenAI client
    client = OpenAI()

    # Structured API call to extract instructions
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": str(json_input),
            }
        ],
        response_format=Pictures,  # Parse into the defined schema
    )

    # Extract the parsed instructions
    instructions = [choice.message.parsed for choice in completion.choices]
    
    instructions_dicts = [instr.dict() for instr in instructions]
    
    output_json = json.dumps(instructions_dicts, ensure_ascii=False, indent=4)

    
    # save the output as a json file
    with open(output_dir / "docling_pictures.json", "w", encoding="utf-8") as file:
        file.write(output_json)

    # Output the results as JSON
    return output_json

def calculate_center_in_json(data, heigth):
    """
    Recursively iterates over JSON data to find entries with 'bbox',
    calculates the center of the bounding box, and adds it as 'center'.
    
    Args:
        data (dict or list): The JSON object to process.
    
    Returns:
        dict or list: The updated JSON object with centers added to bboxes.
    """
    
    
    if isinstance(data, dict):
        # If current level is a dictionary
        if 'bbox' in data and isinstance(data['bbox'], dict):
            bbox = data['bbox']
            if all(key in bbox for key in ['l', 't', 'r', 'b']):
                # Calculate center
                center_x = height - (bbox['l'] + bbox['r']) / 2
                center_y = height - (bbox['b'] + bbox['t']) / 2
                # Add center as a tuple of integers
                data['bbox']['center'] = (int(center_x), int(center_y))
        # Recursively process nested dictionaries
        for key, value in data.items():
            calculate_center_in_json(value, height)
    elif isinstance(data, list):
        # If current level is a list
        for item in data:
            calculate_center_in_json(item, height)
    return data

def structured_openai_api_call_with_text_json(json_input: dict, system_prompt: str):
    """
    Args:
        json_input (dict): A JSON object containing the instructions to be processed.
        system_prompt (str): The system prompt to guide the model's response.

    Returns:
        List[InstructionStep]: A list of parsed instructions extracted from the JSON input, each containing:
            - step (int): The step number.
            - text (str): The instruction text.
            - picture (bool): Whether a picture is associated with the step.
            - picture_description (str): Description of the picture if applicable.
    """
    output_dir = Path("data/output_docling")

    # Define the JSON structure for the instructions
    class TextBlock(BaseModel):
        page_no: int
        text: str
        center_x: int
        center_y: int

    class Instructions(BaseModel):
        instructions: list[TextBlock]

    # Instantiate OpenAI client
    client = OpenAI()

    # Structured API call to extract instructions
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": str(json_input),
            }
        ],
        response_format=Instructions,  # Parse into the defined schema
    )

    # Extract the parsed instructions
    instructions = [choice.message.parsed for choice in completion.choices]
    
    instructions_dicts = [instr.dict() for instr in instructions]
    
    output_json = json.dumps(instructions_dicts, ensure_ascii=False, indent=4)

    
    # save the output as a json file
    with open(output_dir / "docling_text.json", "w", encoding="utf-8") as file:
        file.write(output_json)

    # Output the results as JSON
    return output_json

# -------------------------------------------------------------------------------------
#                               Combination of methods
# -------------------------------------------------------------------------------------
def add_centers_to_instructions(instructions: dict, centers: dict):
    output_dir = Path("data/output_openai_text")
    
    system_prompt = "Take the given instructions JSON, which contains full instruction text, \
        and determine the center points for each instruction based on smaller text snippets provided in another JSON. Specifically:\
        1. Use the smaller text snippets with their center locations to identify which snippets belong to each instruction.\
        2. If a text snippet belongs to an instruction, add its center to a 'center list' in the instructions JSON.\
        Work with the full instructions and ensure the centers are added only for snippets that match the corresponding instruction"
    
    
    # Define the JSON structure for the instructions
    class Centers(BaseModel):
        center_x: int
        center_y: int
    class Instructions(BaseModel):
        step: int
        text: str
        picture: bool
        picture_description: str
        centers: list[Centers]
        
    class Pages(BaseModel):
        page_no: int
        instructions: list[Instructions]

    class pdf(BaseModel):
        pdf_document: list[Pages]
        

    # Instantiate OpenAI client
    client = OpenAI()

    # Structured API call to extract instructions
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt + str(instructions)
            },
            {
                "role": "user",
                "content": str(centers),
            }
        ],
        response_format=pdf,  # Parse into the defined schema
    )

    # Extract the parsed instructions
    instructions = [choice.message.parsed for choice in completion.choices]
    
    instructions_dicts = [instr.dict() for instr in instructions]
    
    output_json = json.dumps(instructions_dicts, ensure_ascii=False, indent=4)

    
    # save the output as a json file
    with open(output_dir / "openai_instructions_with_centers.json", "w", encoding="utf-8") as file:
        file.write(output_json)

    # Output the results as JSON
    return output_json

# ------------------------------------------------------------------------------------------------
# extract all the pictures from the pdf and store them in a pictures folder 
# ------------------------------------------------------------------------------------------------
def extract_images_from_pdf(pdf_path, output_folder):
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    
    # Iterate through each page
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        images = page.get_images(full=True)
        
        # print the number of images on each page
        print(f"Page {page_number+1}: {len(images)} images")
        
        # Extract each image
        for image_index, img in enumerate(images):
            xref = img[0]

            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"{output_folder}/image_{page_number+1}_{image_index+1}.jpg"
            
            # Save the image
            with open(image_filename, "wb") as image_file:
                image_file.write(image_bytes)
                
            # create the image filename
            # image_filename = f"{output_folder}/image_{page_number+1}_{image_index+1}.png"
            
            # # Convert image bytes to a PNG file using Pillow
            # with BytesIO(image_bytes) as image_file:
            #     image = Image.open(image_file)
            #     image.save(image_filename, "PNG")
                
def delete_recurring_images(directory):
    hashes = set()
    to_delete = set()
    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)
        digest = hashlib.sha1(open(path,'rb').read()).digest()
        if digest not in hashes:
            hashes.add(digest)
        else:
            os.remove(path)
            # delete original file (which added this hash) aswell
            to_delete.add(digest)
            
    for digest in to_delete:
        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if hashlib.sha1(open(path,'rb').read()).digest() == digest:
                os.remove(path)
                            
def delete_small_images(directory):
    # 10 KB
    size_limit = 3 * 1024

    # Loop through each file in the directory
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        # Check if it's a file (and not a directory) and its size
        if os.path.isfile(filepath):
            file_size = os.path.getsize(filepath)
            
            # If file size is smaller than the limit, delete it
            if file_size < size_limit:
                print(f"Deleting: {filename}, Size: {file_size} bytes")
                os.remove(filepath)

    #print("Done!")

def merge_json_with_duplicate_removal(json1_path, json2_path, output_path):
    # Load the first JSON file
    with open(json1_path, 'r') as file1:
        json1 = json.load(file1)
    
    # Load the second JSON file
    with open(json2_path, 'r') as file2:
        json2 = json.load(file2)[0]['pictures']
    
    # Merge the data
    combined_data = json1['page'] + json2
    
    # Remove duplicates
    unique_pictures = []
    for pic1 in combined_data:
        is_duplicate = False
        for pic2 in unique_pictures:
            if (pic1['page_no'] == pic2['page_no'] and
                math.isclose(pic1['center_x'], pic2['center_x'], abs_tol=20) and
                math.isclose(pic1['center_y'], pic2['center_y'], abs_tol=20)):
                is_duplicate = True
                print("duplicate found")
                break
        if not is_duplicate:
            unique_pictures.append(pic1)
    
    # Write the result to a new JSON file
    with open(output_path, 'w') as output_file:
        json.dump({"page": unique_pictures}, output_file, indent=4)
    print(f"Combined JSON written to {output_path}")

def move_pictures_from_json(json_path, destination_folder):
    # Create the destination folder if it doesn't exist
    os.makedirs(destination_folder, exist_ok=True)

    # Load the combined JSON
    with open(json_path, 'r') as file:
        data = json.load(file)
    
    # Extract picture URIs
    pictures = [pic['picture_uri'] for pic in data['page']]

    # Move each picture to the destination folder
    for picture in pictures:
        # Normalize file paths
        source_path = os.path.normpath(picture)
        file_name = os.path.basename(source_path)
        destination_path = os.path.join(destination_folder, file_name)

        try:
            # Copy the file to the destination
            shutil.copy(source_path, destination_path)
            print(f"Moved: {source_path} -> {destination_path}")
        except FileNotFoundError:
            print(f"File not found: {source_path}. Skipping...")
        except Exception as e:
            print(f"Error moving {source_path}: {e}")

def logo_decision(img):
    img_uri = get_img_uri(img)
    
    system_prompt = "i have pictures from a work instruction on how to assemble something. \
        Does this image show a step in the assembly process with good information of is it \
        just a label / logo? Set to true if it is a logo and false if it is a step in the assembly process."
    
    client = OpenAI()

    # Define the JSON structure for the instructions
    class Logo(BaseModel):
        is_logo: bool

    # Structured API call to extract instructions
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": img_uri,
                        },
                    },
                ],
            }
        ],
        response_format=Logo,  # Parse into the defined schema
    )

    # Extract the parsed instructions
    instructions = [choice.message.parsed for choice in completion.choices]

    # Output the results as JSON
    return instructions

def delete_all_logos(input_folder = "data/output_all_pictures"):
    # iterate over all images in the folder
    for filename in os.listdir(input_folder):
        path = os.path.join(input_folder, filename)
        img = Image.open(path)
        
        # check if the image is a logo
        is_logo = logo_decision(img)
        # print(is_logo)
        
        
        decision = [instr.dict() for instr in is_logo]
        
        # print(decision)
        
        # if the image is a logo -> delete it
        if decision[0]['is_logo']:
            os.remove(path)
            print(f"Deleted: {path}")

def Convert_PDF_to_JSON():
    # does the pipeline have to be cleared after each run? -> how long does it take to run the pipeline? 
    # -> dependant on that we want to clear the pipeline -> probably want to store
    
    
    # -------------------------------------- docling --------------------------------------
    docling_json = extract_text_and_pictures()
    
    # Load the JSON data from the docling extraction if needed
    # with open("data/output_docling/w5.json", "r", encoding="utf-8") as file:
        # json_data = json.load(file)
        
    # get height of pdf
    try:
        height = docling_json["pages"]["1"]["size"]["height"]
    except:
        height = 842
        print("height not found")
        
    json_data_with_centers = calculate_center_in_json(docling_json, height)   
    # convert into nice jsons
    prompt_picture_json = "Take the input json and extract the pictures. For each picture, provide the page number, picture URI, and center coordinates."
    promt_text_json = "Take the input json and extract the text. For each text block, provide the page number, text, and center coordinates."
    structured_openai_api_call_with_picture_json(json_data_with_centers, prompt_picture_json)
    centers = structured_openai_api_call_with_text_json(json_data_with_centers, promt_text_json)
        
    # -------------------------------------- openai --------------------------------------
    instructions_openai = extract_text_from_pdf() 
    
    
    # ------------------------------------ merge text -----------------------------------
    # read in the json files
    # with open("data/output_openai_text/instructions_by_page.json", "r", encoding="utf-8") as file:
    #     instructions_openai = json.load(file)
        
    # with open("data/output_docling/docling_text.json", "r", encoding="utf-8") as file:
    #     centers = json.load(file)

    add_centers_to_instructions(instructions_openai, centers)
    
    
    # ------------------------------------ picture extraction simple -----------------------------------
    # output folder
    output_folder_simple_picture_extraction = "data/output_pictures"

    # clear output_pictures
    for file in os.listdir(output_folder_simple_picture_extraction):
        os.remove(os.path.join(output_folder_simple_picture_extraction, file))
        
        
    pdf_path = "data/input_pdf/w5.pdf"


    # extract_images_from_pdf(pdf_path, output_folder_simple_picture_extraction)
    # delete_recurring_images(output_folder_simple_picture_extraction)    
    # delete_small_images(output_folder_simple_picture_extraction)
    
    
    extract_pictures(pdf_path, output_folder_simple_picture_extraction)


    # ------------------------------------ merge pictures -----------------------------------
    merge_json_with_duplicate_removal('data/output_pictures/pictures.json', 'data/output_docling/docling_pictures.json', 'data/output_openai_text/combined.json')
    move_pictures_from_json('data/output_openai_text/combined.json', 'data/output_all_pictures')
    
    delete_recurring_images('data/output_all_pictures')
    delete_small_images('data/output_all_pictures')
    
    # ------------------------------------ delete logos -----------------------------------
    delete_all_logos()


# ----------------------------------------------------------------------------------------
#                                     Command line
# ----------------------------------------------------------------------------------------
# extract_text_and_pictures() # docling
# extract_text_from_pdf() # openai

# with open("data/output_docling/w5.json", "r", encoding="utf-8") as file:
#     json_data = json.load(file)

# try:
#     height = json_data["pages"]["1"]["size"]["height"]
# except:
#     height = 842
#     print("height not found")
    
# Calculate centers for bounding boxes in the JSON data
# json_data_with_centers = calculate_center_in_json(json_data, height)

# convert into nice jsons
# prompt_picture_json = "Take the input json and extract the pictures. For each picture, provide the page number, picture URI, and center coordinates."
# promt_text_json = "Take the input json and extract the text. For each text block, provide the page number, text, and center coordinates."
# structured_openai_api_call_with_picture_json(json_data_with_centers, prompt_picture_json)
# centers = structured_openai_api_call_with_text_json(json_data_with_centers, promt_text_json)

# # read in the json files
# with open("data/output_openai_text/instructions_by_page.json", "r", encoding="utf-8") as file:
#     instructions_openai = json.load(file)
    
# with open("data/output_docling/docling_text.json", "r", encoding="utf-8") as file:
#     centers = json.load(file)

# add_centers_to_instructions(instructions_openai, centers)

# output folder
# output_folder = "data/output_pictures"

# clear output_pictures
# for file in os.listdir(output_folder):
#     os.remove(os.path.join(output_folder, file))
    
    
# pdf_path = "data/input_pdf/w5.pdf"


# extract_images_from_pdf(pdf_path, output_folder)
# delete_recurring_images(output_folder)    
# delete_small_images(output_folder)


# merge_json_with_duplicate_removal('data/output_pictures/pictures.json', 'data/output_docling/docling_pictures.json', 'data/output_openai_text/combined.json')

# move_pictures_from_json('data/output_openai_text/combined.json', 'data/output_all_pictures')
# move_pictures_from_json('data/output_openai_text/combined.json', 'data/output_all_pictures')
# delete_all_logos()
Convert_PDF_to_JSON()