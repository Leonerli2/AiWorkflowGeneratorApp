from flask import Flask, request, render_template_string
import qrcode
import os
import shutil
from pathlib import Path
import socket


app = Flask(__name__)

# HTML template for the upload page
upload_form = """
<!doctype html>
<title>Upload File</title>
<h1>Upload Video File</h1>
<form method="post" enctype="multipart/form-data">
    <input type="file" name="file">
    <input type="submit" value="Upload">
</form>
"""

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"
        file = request.files["file"]
        if file.filename == "":
            return "No selected file"
        # Save the file to a directory
        print("Saving file...")
        file.save(f"./uploads/{file.filename}")
        print("File saved successfully!")
        move_to_video_folder2()
        return f"File {file.filename} uploaded successfully!"
    return render_template_string(upload_form)

def move_to_Video_folder():
    # convert the file to a .mp4 file if not a mp4 file
    os.system("ffmpeg -i ./uploads/*.mov ./uploads/*.mp4")
    
    # count how many files are in the video folder
    video_folder = "./Video/"
    video_files = os.listdir(video_folder)
    num_files = len(video_files)

    # rename the file uploaded to the uploads folder to Video[num_files+1].mp4
    src = "./uploads/"
    dst = "./Video/"
    files = os.listdir(src)
    for f in files:
        shutil.move(src + f, dst + f"Video{num_files+1}.mp4")
        
def move_to_video_folder2():
    # Define paths
    uploads_folder = "./uploads/"
    video_folder = "./Videos/"
    os.makedirs(video_folder, exist_ok=True)  # Ensure the Video folder exists

    # Convert non-MP4 files to MP4 using ffmpeg
    for file_name in os.listdir(uploads_folder):
        file_path = os.path.join(uploads_folder, file_name)
        if not file_name.lower().endswith(".mp4"):
            converted_name = f"{Path(file_name).stem}.mp4"
            converted_path = os.path.join(uploads_folder, converted_name)
            os.system(f"ffmpeg -i \"{file_path}\" \"{converted_path}\"")
            os.remove(file_path)  # Remove the original file after conversion

    # Get the current count of files in the Video folder
    video_files = os.listdir(video_folder)
    num_files = len(video_files)

    # Move and rename files
    for file_name in os.listdir(uploads_folder):
        file_path = os.path.join(uploads_folder, file_name)
        new_name = f"Video{num_files + 1}.mp4"
        new_path = os.path.join(video_folder, new_name)
        shutil.move(file_path, new_path)
        num_files += 1  # Increment the file counter for unique naming

    
    
        

if __name__ == "__main__":
    import os

    # Create upload directory if it doesn't exist
    os.makedirs("./uploads", exist_ok=True)
    
    # Generate the QR code
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR code
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Error correction level
        box_size=10,  # Size of each box in the QR code grid
        border=4,  # Border width in boxes
    )
    # get ip address 
    def get_local_ip():
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip

    #print(f"Local IP Address: {get_local_ip()}")
    
    url = "http://" + get_local_ip() + ":5000"
    print(url)
    
    qr.add_data(url)
    qr.make(fit=True)

    # Create an image of the QR code
    img = qr.make_image(fill_color="black", back_color="white")

    # Save the QR code to a file
    img.save("upload_url_qr.png")

    print("QR code saved as upload_url_qr.png")


    # Run the server
    app.run(host="0.0.0.0", port=5000)
    
    
