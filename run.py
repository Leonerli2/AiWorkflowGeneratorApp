import subprocess

# Run file1.py and file2.py simultaneously
process1 = subprocess.Popen(["python", "video_upload.py"])
process2 = subprocess.Popen(["python", "GUI2.py"])

# Wait for both processes to complete
process1.wait()
process2.wait()
