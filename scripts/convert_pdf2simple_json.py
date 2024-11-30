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
        model="gpt-4o",
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
            "Extract all work instructions form the image, this is the most important part and keep the wording. Order them in steps. \
            Say if there is a corresponding picture (true/false) and add a picture short \
            description if applicable. Make sure to only use character that 'charmap' codec can decode."
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

def calculate_center_in_json(data, height):
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
                center_x = (bbox['l'] + bbox['r']) / 2
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

def combine_centers(json_data):
    # Iterate through each document and its pages
    for document in json_data:
        for page in document.get("pdf_document", []):
            for instruction in page.get("instructions", []):
                # Extract centers
                centers = instruction.get("centers", [])
                if centers:
                    # Calculate the average of x and y coordinates
                    avg_center_x = sum(center["center_x"] for center in centers) / len(centers)
                    avg_center_y = sum(center["center_y"] for center in centers) / len(centers)
                    # Replace centers with the average center
                    instruction["centers"] = [{"center_x": avg_center_x, "center_y": avg_center_y}]
                # if centers is empty, add a default center
                else:
                    instruction["centers"] = [{"center_x": 0, "center_y": 0}]
                    
    # save it 
    output_dir = Path("data/output_openai_text")
    output_json = json.dumps(json_data, ensure_ascii=False, indent=4)
    with open(output_dir / "instructions_with_one_center.json", "w", encoding="utf-8") as file:
        file.write(output_json)
    
    
    return json_data

# -------------------------------------------------------------------------------------
#                               Combination of methods
# -------------------------------------------------------------------------------------
def add_centers_to_instructions(instructions: dict, centers: dict):
    output_dir = Path("data/output_openai_text")
    
    system_prompt = "Take the given instructions JSON, which contains full instruction text, \
        and determine the center points for each instruction based on smaller text snippets provided in another JSON. Specifically:\
        1. Use the smaller text snippets and identify which snippets belong to each instruction.\
        2. If a text snippet belongs to an instruction, add its center to a 'center list' in the instructions JSON.\
        3. Try to add atleast one center to each instruction.\
        4. Do this fo every page\
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
        model="gpt-4o",
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
            print("Deleted: ", path)
            # delete original file (which added this hash) aswell
            to_delete.add(digest)
            
    for digest in to_delete:
        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if hashlib.sha1(open(path,'rb').read()).digest() == digest:
                os.remove(path)
                print("Deleted: ", path)
                            
def delete_small_images(directory, number_of_pages):
    # 10 KB
    size_limit = 5 * 1024
    count = 0
    
    

    # Loop through each file in the directory
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        # Check if it's a file (and not a directory) and its size
        if os.path.isfile(filepath):
            file_size = os.path.getsize(filepath)
            
            # If file size is smaller than the limit and is a jpg, delete it
            if file_size < size_limit and filename.endswith(".jpg"):
                print(f"Deleting: {filename}, Size: {file_size} bytes")
                os.remove(filepath)
                count += 1

    if count >= 4 * number_of_pages:
        print(f"Deleted {count} small images... deleting all images extracted automatically")
        # delete all images starting with image...
        for filename in os.listdir(directory):
            if filename.startswith("image"):
                os.remove(os.path.join(directory, filename))
                print(f"Deleted: {filename}")
        print("SCANNED PDF DETECTED! Try to have a better quality PDF")
        return True
    return False
    #print("Done!")

def merge_json_with_duplicate_removal(json1_path, json2_path, output_path, scanned_pdf):
    if scanned_pdf == False:
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
    else:
        # just take json2
        with open(json2_path, 'r') as file2:
            json2 = json.load(file2)
            
        unique_pictures = json2[0]["pictures"]
        
        # Write the result to a new JSON file
        with open(output_path, 'w') as output_file:
            json.dump({"page": unique_pictures}, output_file, indent=4)

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

def clean_combined_json(input_file = "data/output_openai_text/combined.json", output_file="data/output_openai_text/combined_cleaned.json"):
    with open(input_file, 'r') as f:
        data = json.load(f)

    # New data to hold filtered and updated entries
    processed_data = {"page": []}

    # Directory where valid images reside
    valid_folder = "data\\output_all_pictures"

    # Process each entry
    for entry in data["page"]:
        # Extract file name from the current URI
        file_name = os.path.basename(entry["picture_uri"])

        # Check if the file exists in the valid folder
        new_uri = os.path.join(valid_folder, file_name)
        if os.path.exists(new_uri.replace("\\", os.sep)):  # Adjust for OS path
            # Update the URI
            entry["picture_uri"] = new_uri
            # Add entry to the new data list
            processed_data["page"].append(entry)

    # Write the processed data back to the output file
    with open(output_file, 'w') as f:
        json.dump(processed_data, f, indent=4)
  
# ------------------------------------------------------------------------------------------------
#                                       mapping pictures to instructions
# ------------------------------------------------------------------------------------------------
def map_pictures_to_instructions_with_centers(instructions_json, pictures_json):
    """
    Maps pictures to the closest instructions for each page based on center coordinates.
    
    Parameters:
        instructions_json (list): JSON list of pages, each containing instructions with center coordinates.
        pictures_json (dict): JSON object with picture data including page numbers and coordinates.
    
    Returns:
        list: Updated instructions JSON with a "pictures_array" field added to each instruction.
    """
    
    # Helper function to calculate distance
    def calculate_distance(x1, y1, x2, y2):
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    
    # Iterate through documents in the instructions JSON
    for document in instructions_json:
        for page in document['pdf_document']:
            page_number = page['page_no']
            
            # Get pictures for the current page
            pictures_on_page = [
                picture for picture in pictures_json['page'] if picture['page_no'] == page_number
            ]
            
            # Map pictures to each instruction
            for instruction in page['instructions']:
                if 'centers' in instruction and pictures_on_page:
                    instruction_center = instruction['centers'][0]  # Assuming one center per instruction
                    distances = [
                        (
                            picture['picture_uri'], 
                            calculate_distance(instruction_center['center_x'], instruction_center['center_y'],
                                               picture['center_x'], picture['center_y'])
                        )
                        for picture in pictures_on_page
                    ]
                    # Sort by distance and select closest pictures
                    distances.sort(key=lambda x: x[1])
                    instruction['pictures_array'] = [dist[0] for dist in distances[:1]]
                else:
                    instruction['pictures_array'] = []
    
    return instructions_json

def match_pictures_to_instructions_simple(pictures_json, instructions_json):
    instructions_json = instructions_json[0]
    # Find the closest instruction for each picture
    def find_closest_instruction(picture, instructions):
        closest_instruction = None
        min_distance = float('inf')

        for instruction in instructions:
            for center in instruction['centers']:
                # distance = math.sqrt((picture['center_x'] - center['center_x'])**2 + (picture['center_y'] - center['center_y'])**2)
                distance = abs(picture['center_x'] - center['center_x']) + 10 * abs(picture['center_y'] - center['center_y'])
                if distance < min_distance:
                    min_distance = distance
                    closest_instruction = instruction

        return closest_instruction

    # Iterate over the pictures and find the closest instruction
    for picture in pictures_json['page']:
        page_no = picture['page_no']
        instructions_on_page = [inst for inst in instructions_json['pdf_document'] if inst['page_no'] == page_no]
        
        if not instructions_on_page:
            continue

        instructions_on_page = instructions_on_page[0]['instructions']
        closest_instruction = find_closest_instruction(picture, instructions_on_page)

        if 'pictures_array' not in closest_instruction:
            closest_instruction['pictures_array'] = []
        closest_instruction['pictures_array'].append(picture['picture_uri'])

    return instructions_json 

def map_pictures_and_instructions_by_sequence(instructions_json, pictures_json):
    """
    Maps pictures to instructions based on unified reading order of instructions and pictures.

    Parameters:
        instructions_json (list): List of instruction pages with centers for each instruction.
        pictures_json (dict): Dictionary of pictures grouped by page with centers.

    Returns:
        list: Updated instructions JSON with pictures mapped based on sequence logic.
    """
    for document in instructions_json:
        for page in document['pdf_document']:
            page_number = page['page_no']

            # Get pictures for the current page
            pictures_on_page = [
                {'type': 'picture', 'data': picture}
                for picture in pictures_json['page']
                if picture['page_no'] == page_number
            ]

            # Get instructions for the current page
            instructions_on_page = [
                {'type': 'instruction', 'data': instruction}
                for instruction in page['instructions']
            ]

            # Combine and sort by reading order
            combined = sorted(
                pictures_on_page + instructions_on_page,
                key=lambda item: (
                        item['data']['centers'][0]['center_y'] if 'centers' in item['data'] else item['data']['center_y'],
                        item['data']['centers'][0]['center_x'] if 'centers' in item['data'] else item['data']['center_x']
                )
            )

            # Sequentially process the sorted elements
            pending_instructions = []
            last_instruction = None
            for item in combined:
                if item['type'] == 'instruction':
                    instruction = item['data']
                    if instruction['picture']:
                        # If this instruction needs a picture, add to pending list
                        pending_instructions.append(instruction)
                    else:
                        # Ensure no pictures are mapped
                        instruction['pictures_array'] = []
                    last_instruction = instruction
                elif item['type'] == 'picture':
                    picture = item['data']
                    if pending_instructions:
                        # Assign the picture to all pending instructions
                        for pending in pending_instructions:
                            if 'pictures_array' not in pending:
                                pending['pictures_array'] = []
                            pending['pictures_array'].append(picture['picture_uri'])
                        pending_instructions.clear()
                    else:
                        # Map the picture to the last seen instruction if no pending instructions
                        if last_instruction:
                            if 'pictures_array' not in last_instruction:
                                last_instruction['pictures_array'] = []
                            last_instruction['pictures_array'].append(picture['picture_uri'])

    return instructions_json


def find_closest_instruction_to_instruction(target_instruction, instructions):
    """
    Finds the closest instruction to the target instruction based on (center_x, center_y).
    """
    closest_instruction = None
    min_distance = float('inf')

    for instruction in instructions:
        # Skip the target itself
        if instruction == target_instruction:
            continue

        # Skip instructions without a pictures array
        if 'pictures_array' not in instruction:
            continue

        for center in instruction['centers']:
            for target_center in target_instruction['centers']:
                # Calculate distance
                distance = abs(target_center['center_x'] - center['center_x']) + 10 * abs(target_center['center_y'] - center['center_y'])
                if distance < min_distance:
                    min_distance = distance
                    closest_instruction = instruction

    return closest_instruction
def match_pictures_to_instructions2(pictures_json, instructions_json):
    """
    Maps pictures to instructions, ensuring "picture" == False instructions are skipped.
    Ensures any instruction with "picture" == True but no pictures array gets closest instruction's pictures.
    """
    instructions_json = instructions_json[0]

    # Find the closest instruction for each picture
    def find_closest_instruction(picture, instructions):
        closest_instruction = None
        min_distance = float('inf')

        for instruction in instructions:
            # Skip instructions where "picture" is False
            if not instruction.get("picture", False):
                continue

            for center in instruction['centers']:
                # Calculate distance with higher weight for vertical proximity
                distance = abs(picture['center_x'] - center['center_x']) + 10 * abs(picture['center_y'] - center['center_y'])
                if distance < min_distance:
                    min_distance = distance
                    closest_instruction = instruction

        return closest_instruction

    # Iterate over the pictures and find the closest instruction
    for picture in pictures_json['page']:
        page_no = picture['page_no']
        instructions_on_page = [inst for inst in instructions_json['pdf_document'] if inst['page_no'] == page_no]
        
        if not instructions_on_page:
            continue

        instructions_on_page = instructions_on_page[0]['instructions']
        closest_instruction = find_closest_instruction(picture, instructions_on_page)

        # Skip if no valid instruction is found
        if not closest_instruction:
            continue

        # Assign picture to the closest instruction
        if 'pictures_array' not in closest_instruction:
            closest_instruction['pictures_array'] = []
        closest_instruction['pictures_array'].append(picture['picture_uri'])

    # Add missing pictures from the closest instruction for "picture" == True
    for document in instructions_json['pdf_document']:
        for instruction in document['instructions']:
            if instruction.get("picture", False) and 'pictures_array' not in instruction:
                # Find the closest instruction with a pictures array
                closest_instruction = find_closest_instruction_to_instruction(instruction, document['instructions'])
                if closest_instruction and 'pictures_array' in closest_instruction:
                    instruction['pictures_array'] = closest_instruction['pictures_array']

    return instructions_json

def dummy_match_pictures_to_instructions(pictures_json, instructions_json):
    # for each page just take the first instruction and add the pictures to it
    for page in instructions_json[0]['pdf_document']:
        if page['instructions']:
            page['instructions'][0]['pictures_array'] = [pic['picture_uri'] for pic in pictures_json['page'] if pic['page_no'] == page['page_no']]
    return instructions_json[0]



def change_image_path(pdf_name, json_file):
    # iterate over the json file and if you find a picture_uri, change the path to the new path 
    base_path = os.path.join("cache", "pictures", pdf_name)
    
    # Iterate over each page in the JSON data
    for page in json_file.get("pdf_document", []):
        for instruction in page.get("instructions", []):
            # Check and update the "pictures_array" if present
            if "pictures_array" in instruction:
                updated_paths = []
                for picture_path in instruction["pictures_array"]:
                    picture_name = os.path.basename(picture_path)
                    updated_paths.append(os.path.join(base_path, picture_name))
                instruction["pictures_array"] = updated_paths
    
    return json_file



# ------------------------------------------------------------------------------------------------
def Convert_PDF_to_JSON(input_workinstruction_pdf_path = "data/workinstructions/w5.pdf"):
    # delete cache if it exists for this pdf
    try:
        shutil.rmtree("cache/pictures/" + input_workinstruction_pdf_path.split("/")[-1].split(".")[0])
        os.remove("cache/jsons/" + input_workinstruction_pdf_path.split("/")[-1].split(".")[0] + ".json")
        print("Deleted cache, converting again...")
    except:
        print("New pdf selected, starting conversion...")
        pass
    try:
        os.remove("cache/jsons/" + input_workinstruction_pdf_path.split("/")[-1].split(".")[0] + "_dummy.json")
        os.remove("cache/jsons/" + input_workinstruction_pdf_path.split("/")[-1].split(".")[0] + "_reading.json")
    except:
        pass
    
    # delete all the files int eh input folder
    for file in os.listdir("data/input_pdf"):
        os.remove(os.path.join("data/input_pdf", file))
    
    # copy the pdf to the input folder
    shutil.copy(input_workinstruction_pdf_path, "data/input_pdf")
    
    
    name_of_pdf = input_workinstruction_pdf_path.split("/")[-1].split(".")[0]
    print("Name of the pdf: ", name_of_pdf)
    
    # get number of pages
    pdf = fitz.open(input_workinstruction_pdf_path)
    number_of_pages = pdf.page_count
    
    # does the pipeline have to be cleared after each run? -> how long does it take to run the pipeline? 
    # -> dependant on that we want to clear the pipeline -> probably want to store
    # clear all the folders: output_docling, output_openai_text, output_pictures, output_all_pictures
    try: 
        for folder in ["data/output_docling/pictures", "data/output_docling", "data/output_openai_text", "data/output_pictures", "data/output_all_pictures"]:
            for file in os.listdir(folder):
                if file != "pictures":
                    os.remove(os.path.join(folder, file))
    except:
        ResourceWarning("Could not find all folders")
    
    
    # -------------------------------------- docling --------------------------------------
    extract_text_and_pictures(input_workinstruction_pdf_path)
    # print(str(docling_document))
    # print("docling_document type: ", type(docling_document))
    # print("docling_document ", docling_document)
    # print(json.dumps(str(docling_document)))
    
    # docling_json= json.dumps(str(docling_document))
    
    
        
    # Load the JSON data from the docling extraction if needed
    with open("data/output_docling/" + name_of_pdf + ".json", "r", encoding="utf-8", errors="replace") as file:
        docling_json = json.load(file)
    # print(type(docling_json))

    # get height of pdf
    try:
        height = docling_json["pages"]["1"]["size"]["height"]
        print("Height found ", height)
    except:
        height = 842
        print(docling_json)
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
    # # read in the json files
    # with open("data/output_openai_text/instructions_by_page.json", "r", encoding="utf-8") as file:
    #     instructions_openai = json.load(file)
        
    # # with open("data/output_docling/docling_text.json", "r", encoding="utf-8") as file:
    #     centers = json.load(file)
    add_centers_to_instructions(instructions_openai, centers)
    
    combine_centers(json.load(open("data/output_openai_text/openai_instructions_with_centers.json")))
    
    
    # ------------------------------------ picture extraction simple -----------------------------------
    # output folder
    output_folder_simple_picture_extraction = "data/output_pictures"

    # clear output_pictures
    for file in os.listdir(output_folder_simple_picture_extraction):
        os.remove(os.path.join(output_folder_simple_picture_extraction, file))
        
        


    # extract_images_from_pdf(pdf_path, output_folder_simple_picture_extraction)
    # delete_recurring_images(output_folder_simple_picture_extraction)    
    # delete_small_images(output_folder_simple_picture_extraction)
    
    
    extract_pictures(input_workinstruction_pdf_path, output_folder_simple_picture_extraction)
    delete_recurring_images(output_folder_simple_picture_extraction)
    scanned_pdf = delete_small_images(output_folder_simple_picture_extraction, number_of_pages)

    # ------------------------------------ merge pictures -----------------------------------
    merge_json_with_duplicate_removal('data/output_pictures/pictures.json', 'data/output_docling/docling_pictures.json', 'data/output_openai_text/combined.json', scanned_pdf)
    move_pictures_from_json('data/output_openai_text/combined.json', 'data/output_all_pictures')
    
    delete_recurring_images('data/output_all_pictures')
    delete_small_images('data/output_all_pictures', number_of_pages)
    
    # ------------------------------------ delete logos -----------------------------------
    delete_all_logos()
    
    clean_combined_json('data/output_openai_text/combined.json')
    
   
    
    instructions_json = json.load(open("data/output_openai_text/instructions_with_one_center.json"))
    pictures_json = json.load(open("data/output_openai_text/combined_cleaned.json"))

    try: 
        finished_json = match_pictures_to_instructions2(pictures_json=pictures_json, instructions_json=instructions_json)
        
        finished_json = change_image_path(name_of_pdf, finished_json)
        
        with open("data/output_openai_text/final_instructions.json", "w") as file:
            json.dump(finished_json, file, indent=4)
        
        # move the final json to cache/jsons/name_of_pdf.json (rename the json)
        shutil.move("data/output_openai_text/final_instructions.json", "cache/jsons/")
        os.rename("cache/jsons/final_instructions.json", "cache/jsons/" + name_of_pdf + ".json")
    except:
        print("Could not match pictures to instructions with distance")
    
    try:
        # finished_json = match_pictures_to_instructions_simple(pictures_json=pictures_json, instructions_json=instructions_json)
        finished_json_reading = map_pictures_and_instructions_by_sequence(instructions_json=instructions_json, pictures_json=pictures_json)
        
        finished_json_reading = change_image_path(name_of_pdf, finished_json_reading[0])
        
        with open("data/output_openai_text/final_instructions_reading.json", "w") as file:
            json.dump(finished_json_reading, file, indent=4)
            
        # move the final json to cache/jsons/name_of_pdf.json (rename the json)
        shutil.move("data/output_openai_text/final_instructions_reading.json", "cache/jsons/")
        os.rename("cache/jsons/final_instructions_reading.json", "cache/jsons/" + name_of_pdf + "_reading.json")
    except:
        print("Could not match pictures to instructions with reading order")
        

    finished_json_dummy = dummy_match_pictures_to_instructions(pictures_json=pictures_json, instructions_json=instructions_json)
    finished_json_dummy = change_image_path(name_of_pdf, finished_json_dummy)
    with open("data/output_openai_text/final_instructions_dummy.json", "w") as file:
        json.dump(finished_json_dummy, file, indent=4)
    
    # move the final json to cache/jsons/name_of_pdf.json (rename the json)
    shutil.move("data/output_openai_text/final_instructions_dummy.json", "cache/jsons/")
    os.rename("cache/jsons/final_instructions_dummy.json", "cache/jsons/" + name_of_pdf + "_dummy.json")
    # except:
    #     print("Could not match pictures to instructions with dummy")
    
    # move all pictures to cache/pictures/name_of_pdf
    # make dir 
    os.makedirs("cache/pictures/" + name_of_pdf, exist_ok=True)
    for file in os.listdir("data/output_all_pictures"):
        shutil.move("data/output_all_pictures/" + file, "cache/pictures/" + name_of_pdf + "/" + file)


# ----------------------------------------------------------------------------------------
#                                     Command line
# ----------------------------------------------------------------------------------------
# Convert_PDF_to_JSON()

# instructions_json = json.load(open("data/output_openai_text/instructions_with_one_center.json"))
# pictures_json = json.load(open("data/output_openai_text/combined_cleaned.json"))

# finished_json_reading = map_pictures_and_instructions_by_sequence(instructions_json=instructions_json, pictures_json=pictures_json)
            
# with open("data/output_openai_text/final_instructions_reading.json", "w") as file:
#     json.dump(finished_json_reading, file, indent=4)

# finished_json = match_pictures_to_instructions_simple(pictures_json=pictures_json, instructions_json=instructions_json)

# name_of_pdf = "w7"
# instructions_json = json.load(open("data/output_openai_text/instructions_with_one_center.json"))
# pictures_json = json.load(open("data/output_openai_text/combined_cleaned.json"))
# finished_json_reading = map_pictures_and_instructions_by_sequence(instructions_json=instructions_json, pictures_json=pictures_json)

# finished_json_reading = change_image_path(name_of_pdf, finished_json_reading[0])

# with open("data/output_openai_text/final_instructions_reading.json", "w") as file:
#     json.dump(finished_json_reading, file, indent=4)