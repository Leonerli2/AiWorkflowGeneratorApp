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
        response_format=InstructionStep,  # Parse into the defined schema
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
    
    client = OpenAI()
    
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

def extract_text_from_pdf():
    # get current working directory
    cwd = Path.cwd()
    
    input_path_folder = cwd / "data/input_pdf"
    output_path_folder_images = cwd / "data/output_images"
    
    pdf_files = list(input_path_folder.glob("*.pdf"))
    
    images = convert_pdfs_to_images(input_path_folder)
    
    #save the images in output folder
    for i, img in enumerate(images):
        img.save(output_path_folder_images / f"page_{i}.jpg")
        
        
extract_text_from_pdf()