from moviepy.editor import VideoFileClip
from openai import OpenAI
import json
import cv2

def extract_audio(video_path, audio_output="speech.mp3"):
    # Load the video file
    video = VideoFileClip(video_path)
    
    # Extract the audio
    audio = video.audio
    
    # Write the audio file
    audio.write_audiofile(audio_output)
    
    # Close the video file to free up resources
    video.close()
    
def load_video(video_path):
    # Load the video file and return the VideoFileClip object
    video = VideoFileClip(video_path)
    return video

def audio_text_extraction_timestamps(audio_file_path, json_file_path = "src/transcript.json"):
    client = OpenAI(api_key="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")
  

    audio_file = open(audio_file_path, "rb")
    transcript = client.audio.transcriptions.create(
    file=audio_file,
    model="whisper-1",
    response_format="verbose_json",
    timestamp_granularities=["word"]
    )
    # Store the transcript data in a JSON file
    
    with open(json_file_path, "w") as json_file:
        json.dump(transcript.model_dump(), json_file, indent=4)
    
    return transcript.words

def extract_instructions_from_text(json_input_path, json_output_path):
    # Load the JSON file
    with open(json_input_path, 'r') as file:
        transcript_data = json.load(file)

   
    client = OpenAI(api_key="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")
    prompt_detailed = f"""Sie haben eine Transkriptions-JSON mit einer kompletten Arbeitsanweisung, die jeweils Zeitstempel und gesprochenen Text enthalten.
        Bitte extrahiren sie jeden einzelnen Schritt der Arbeitsanweisung und führen sie die folgenden Schritte aus:
        1. Extrahieren Sie die Beschreibung des Arbeitsschritts.
        2. Überprüfen Sie, ob das Wort "Foto" im Text erwähnt wird:
        - Falls "Foto" erscheint, notieren Sie den Zeitstempel, an dem es zuerst erwähnt wird.
        - Falls "Foto" nicht erwähnt wird, setzen Sie dieses Feld auf null.
        3. Geben Sie jede Arbeitsanweisung zurück mit:
        - Zeitstempeln für Beginn und Ende der jeweiligen Anweisung,
        - Einem separaten Eintrag für den "Foto"-Zeitstempel oder null.

        Hier ist die zu analysierende Transkriptions-JSON:
        {transcript_data}
        
        verwende folgende output struktur: 
    
        "steps": [
            (
                "description": "Blech mit Schwei\u00dfbolzen nehmen, einsetzen.",
                "start_time": 2.2200000286102295,
                "end_time": 5.440000057220459,
                "photo_timestamp": 6.480000019073486
            ),
            (
                "description": "Distanzst\u00fcck mit Loch nehmen, auch einsetzen.",
                "start_time": 7.71999979019165,
                "end_time": 11.65999984741211,
                "photo_timestamp": 11.65999984741211
            )
            ]
        
        """
    text = transcript_data
    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Sie sind ein Assistent, der JSON-Transkriptionsdaten verarbeitet."},
            {"role": "user", "content": prompt_detailed}
        ],
        response_format={"type": "json_object"}
    )
    
    # Convert the message content to JSON and store it
    instructions_json = json.loads(response.choices[0].message.content)
    with open(json_output_path, "w") as json_file:
        json.dump(instructions_json, json_file, indent=4)



def extract_frames(video_nr, video_path, instructions_json_path, output_dir):
    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # load json
    with open(instructions_json_path, 'r') as file:
        instructions_json = json.load(file)

    # Get the video's frame rate
    fps = cap.get(cv2.CAP_PROP_FPS)

    for idx, step in enumerate(instructions_json["steps"]):

        description = step["description"]
        start_time = step["start_time"]
        end_time = step["end_time"]
        photo_time = step["photo_timestamp"]

        if photo_time is not None:
            # print(f"Extracting frame for step {idx + 1}: {description}")
            time = photo_time
        else:  
            time = end_time


        # Calculate the frame number for each timestamp
        frame_number = int(time * fps)
        # Set the video position to the frame number
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        # Read the frame
        ret, frame = cap.read()

        if ret:
            # Save the frame as an image file
            output_path = f"{output_dir}/instruction{video_nr}_{idx+1}.jpg"
            cv2.imwrite(output_path, frame)
        else:
            print(f"Could not extract frame at {time}s")

    # Release the video capture object
    cap.release()

