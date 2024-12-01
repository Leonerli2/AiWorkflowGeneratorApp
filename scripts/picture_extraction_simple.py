import fitz
import hashlib
import pandas as pd
import os
import json

pdf_path = "data/input_pdf/w5.pdf"

# Function to convert DataFrame to JSON structure
def dataframe_to_json(df):
    return {
        "page": [
            {
                "page_no": row["page"],
                "picture_uri": f"data\\output_pictures\\{row['image_filename']}",
                "center_x": row["center_x"],
                "center_y": row["center_y"]
            }
            for _, row in df.iterrows()
        ]
    }
    
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

def extract_pictures(pdf_path, output_folder = "data/output_pictures"):
    doc = fitz.open(pdf_path)

    data = []

    # create dataframe for pictures 
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_number = page_num + 1
        page_width = page.mediabox.width
        page_height = page.mediabox.height

        # Get list of images on the page
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list, start=1):
            xref = img[0]
            # Attempt to get the image rectangle (position)
            rects = page.get_image_rects(xref)
            if rects:
                bbox = rects[0]  # Assuming one rectangle per image
                # Extract the image bytes
                try:
                    image_info = doc.extract_image(xref)
                    image_bytes = image_info["image"]
                    # Compute the image hash
                    hash_image = hashlib.sha1(image_bytes).hexdigest()
                except Exception as e:
                    print(f"Error extracting image at page {page_number}, xref {xref}: {e}")
                    hash_image = None

                # print(f"Found image xref {xref} on page {page_number}: {bbox}")
                # Append data to the list
                data.append({
                    'page': page_number,
                    'x0': bbox.x0,
                    'y0': bbox.y0,
                    'x1': bbox.x1,
                    'y1': bbox.y1,
                    # 'width': bbox.width,
                    # 'height': bbox.height,
                    'image_hash': hash_image,
                    'image_filename': None
                })
            else:
                print(f"No position found for image xref {xref} on page {page_number}.")
                
    extract_images_from_pdf(pdf_path, output_folder)
    
    
    # Create DataFrame
    df = pd.DataFrame(data)

    # deleta all the images in df with the hashes are not corresponding to one picture in the output folder
    # Get a list of image hashes from the output folder
    output_image_hashes = []
    output_image_filenames = []
    for filename in os.listdir(output_folder):
        if filename.endswith((".jpg", ".jpeg")):
            with open(os.path.join(output_folder, filename), "rb") as img_file:
                img_hash = hashlib.sha1(img_file.read()).hexdigest()
                output_image_hashes.append(img_hash)
                output_image_filenames.append(filename)

    # Filter the DataFrame to keep only rows with image hashes that are in the output folder
    for i, row in df.iterrows():
        if row['image_hash'] not in output_image_hashes:
            df.drop(i, inplace=True)
        else:
            df.at[i, 'image_filename'] = output_image_filenames[output_image_hashes.index(row['image_hash'])]

    # Reset the index of the DataFrame
    df.reset_index(drop=True, inplace=True)


    # check if all output images are in the df
    print("Checking for missing hashes...")
    for hash in output_image_hashes:
        if hash not in df['image_hash'].values:
            print(f"Image hash {hash} not found in DataFrame")
    print("Done!")

    # calculate the center of the image and add it to the df
    df['center_x'] = (df['x0'] + df['x1']) / 2
    df['center_y'] = (df['y0'] + df['y1']) / 2

    # delete the columns x0, y0, x1, y1 and image_hash
    df.drop(columns=['x0', 'y0', 'x1', 'y1', 'image_hash'], inplace=True)

    print(df.head())


    # Convert to JSON
    json_structure = dataframe_to_json(df)
    json_result = json.dumps(json_structure, indent=4)

    # print(json_result)
    
    # save the json file
    with open("data/output_pictures/pictures.json", "w") as json_file:
        json_file.write(json_result)
        
    return json_result

# extract_pictures(pdf_path)